import streamlit as st
from datetime import datetime

from auth_google import iniciar_login, procesar_callback, cargar_credenciales
from pdf_reader import extraer_texto_pdf
from drive_utils import listar_pdfs_drive, descargar_pdf_drive
from calendar_utils import crear_evento_calendar, obtener_eventos_calendar
from analyzer import calcular_fecha_limite, buscar_asunto, calcular_fecha_agenda
from ai_extractor import extraer_entidades_ia

st.set_page_config(
    page_title="Gestor Inteligente de Documentos (IA)",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    # 📑 Gestor Inteligente de PDFs (IA)
    ### Analisis con reglas + IA (fallback)
    """
)

st.caption("Analiza documentos usando solo IA.")
st.divider()

procesar_callback()
from auth_google import obtener_usuario

if st.session_state.get("just_logged_in"):
    st.components.v1.html(
        """
        <script>
        try {
            localStorage.setItem('oauth_done', '1');
            if (window.opener) {
                window.opener.postMessage({oauth_done: 1}, '*');
            }
            window.close();
        } catch (e) { }
        </script>
        """,
        height=0,
        unsafe_allow_html=True,
    )
    st.session_state["just_logged_in"] = False

st.session_state.setdefault("credentials", None)
st.session_state.setdefault("eventos_creados", set())

if not st.session_state.get("credentials"):
    creds_guardadas = cargar_credenciales()
    if creds_guardadas:
        st.session_state.credentials = creds_guardadas

if st.session_state.get("credentials") and "user_info" not in st.session_state:
    st.session_state.user_info = obtener_usuario(st.session_state.get("credentials"))

accion_default = "Tarea"

col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("Fuentes de documentos")

    with st.container(border=True):
        st.markdown("### Google Drive")
        st.caption("Carga y analiza PDFs desde tu cuenta de Google")

        if st.button("Cargar PDFs desde Drive", use_container_width=True):
            if not st.session_state.credentials:
                st.warning("Debes iniciar sesion para acceder a Google Drive.")
            else:
                with st.spinner("Conectando con Google Drive..."):
                    st.session_state.archivos_drive = listar_pdfs_drive(
                        st.session_state.get("credentials")
                    )

    with st.container(border=True):
        st.markdown("### Subir desde tu equipo")
        st.caption("Arrastra uno o varios documentos PDF")

        pdfs = st.file_uploader(
            "Selecciona archivos PDF",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed",
        )

        st.session_state.pdfs_locales = pdfs

    with st.container(border=True):
        st.markdown("### Google Calendar")
        st.caption("Eventos agendados y preparados")

        if st.session_state.get("credentials"):
            st.success("Conectado a Google Calendar")

            eventos = obtener_eventos_calendar(st.session_state.get("credentials"), dias=30)

            if eventos:
                st.markdown("#### Proximos eventos (30 dias):")

                for evento in eventos:
                    inicio = evento.get("start", {}).get("dateTime", evento.get("start", {}).get("date", "N/A"))
                    titulo = evento.get("summary", "Sin titulo")
                    descripcion = evento.get("description", "")[:100]

                    try:
                        if "T" in inicio:
                            fecha_obj = datetime.fromisoformat(inicio.replace("Z", "+00:00"))
                            fecha_formateada = fecha_obj.strftime("%d/%m/%Y %H:%M")
                        else:
                            fecha_formateada = inicio
                    except Exception:
                        fecha_formateada = inicio

                    with st.expander(f"{titulo} - {fecha_formateada}"):
                        st.write(f"**Fecha:** {fecha_formateada}")
                        if descripcion:
                            st.write(f"**Detalles:** {descripcion}")
                        enlace = evento.get("htmlLink", "")
                        if enlace:
                            st.markdown(f"[Abrir en Google Calendar]({enlace})")
            else:
                st.info("No hay eventos proximos en los proximos 30 dias")
        else:
            st.warning("Inicia sesion para ver Google Calendar")

with col2:
    st.subheader("Resultados del analisis")

    if "archivos_drive" in st.session_state:
        archivos = st.session_state.archivos_drive

        if archivos:
            seleccionados = st.multiselect(
                "Documentos desde Drive",
                archivos,
                format_func=lambda x: x["name"],
            )

            if seleccionados and st.button("Analizar documentos de Drive", use_container_width=True):
                for archivo in seleccionados:
                    with st.expander(f"{archivo['name']}"):
                        if not st.session_state.get("credentials"):
                            st.warning("Debes iniciar sesion para descargar archivos de Drive.")
                            continue

                        pdf_bytes = descargar_pdf_drive(
                            st.session_state.get("credentials"),
                            archivo["id"],
                        )

                        texto = extraer_texto_pdf(pdf_bytes)

                        asunto = buscar_asunto(texto)
                        ia_info = extraer_entidades_ia(texto)
                        if ia_info.get("error") == "missing_model":
                            st.warning(
                                "Modelo spaCy no instalado. Ejecuta: python -m spacy download es_core_news_sm"
                            )
                            continue

                        encargado = ia_info.get("responsable")
                        fecha_detectada = ia_info.get("fecha_limite")

                        fecha_limite = calcular_fecha_limite(fecha_detectada)
                        fecha_agenda = calcular_fecha_agenda(fecha_detectada)

                        evento_key = f"drive:{archivo['id']}"
                        if evento_key not in st.session_state.eventos_creados:
                            if not st.session_state.get("credentials"):
                                st.warning("Inicia sesion para crear eventos en Google Calendar.")
                            else:
                                crear_evento_calendar(
                                    st.session_state.get("credentials"),
                                    titulo=(
                                        f"{accion_default}: {asunto}"
                                        if asunto
                                        else f"{accion_default}: {archivo['name']}"
                                    ),
                                    descripcion=(
                                        f"Documento analizado: {archivo['name']}\n"
                                        f"Asunto: {asunto if asunto else 'No detectado'}"
                                    ),
                                    fecha_limite=fecha_agenda,
                                )
                                st.session_state.eventos_creados.add(evento_key)
                                st.success("Evento creado en tu Google Calendar")

                        st.caption("IA usada para extraer datos")
                        st.metric("Fecha limite", fecha_limite.strftime("%d/%m/%Y"))
                        st.write("Responsable (IA):", encargado or "No detectado")
                        st.text_area("Vista previa del texto", texto[:3000], height=180)

    if "pdfs_locales" in st.session_state and st.session_state.pdfs_locales:
        st.divider()
        st.markdown("### PDFs locales")

        for pdf in st.session_state.pdfs_locales:
            with st.expander(f"{pdf.name}"):
                texto = extraer_texto_pdf(pdf)

                asunto = buscar_asunto(texto)
                ia_info = extraer_entidades_ia(texto)
                if ia_info.get("error") == "missing_model":
                    st.warning(
                        "Modelo spaCy no instalado. Ejecuta: python -m spacy download es_core_news_sm"
                    )
                    continue

                encargado = ia_info.get("responsable")
                fecha_detectada = ia_info.get("fecha_limite")

                fecha_limite = calcular_fecha_limite(fecha_detectada)
                fecha_agenda = calcular_fecha_agenda(fecha_detectada)

                st.caption("IA usada para extraer datos")

                evento_key = f"local:{pdf.name}"
                if evento_key not in st.session_state.eventos_creados:
                    if not st.session_state.get("credentials"):
                        st.warning("Inicia sesion para crear eventos en Google Calendar.")
                    else:
                        crear_evento_calendar(
                            st.session_state.get("credentials"),
                            titulo=(
                                f"{accion_default}: {asunto}"
                                if asunto
                                else f"{accion_default}: {pdf.name}"
                            ),
                            descripcion=(
                                f"Documento analizado: {pdf.name}\n"
                                f"Asunto: {asunto if asunto else 'No detectado'}"
                            ),
                            fecha_limite=fecha_agenda,
                        )
                        st.session_state.eventos_creados.add(evento_key)
                        st.success("Evento creado en tu Google Calendar")

                st.metric("Fecha limite", fecha_limite.strftime("%d/%m/%Y"))
                st.write("Responsable (IA):", encargado or "No detectado")
                st.text_area("Texto (vista previa)", texto[:3000], height=180)

if not st.session_state.get("credentials"):
    st.warning("No has iniciado sesion")

    if st.button("Iniciar sesion con Google"):
        url = iniciar_login()
        st.markdown(f"[Autorizar aplicacion]({url})")

    st.stop()

st.success("Sesion iniciada correctamente")

with st.sidebar:
    st.markdown("## Usuario conectado")

    usuario = st.session_state.get("user_info", {})
    st.write(f"**Email:** {usuario.get('email', 'No disponible')}")
    st.write(f"**Nombre:** {usuario.get('name', '')}")

    st.divider()

    st.markdown("## Acciones")
    st.markdown("- Analizar PDFs")

    if st.session_state.get("credentials"):
        st.markdown("- Google Calendar conectado")

        if st.button("Cerrar sesion", use_container_width=True):
            from auth_google import eliminar_credenciales

            eliminar_credenciales()
            st.session_state.credentials = None
            st.session_state.user_info = None
            st.rerun()
    else:
        st.markdown("- Google Calendar no configurado")
