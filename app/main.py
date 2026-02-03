import streamlit as st  # interfaz web para la app
from auth_google import iniciar_login, procesar_callback  # funciones de autenticación
from pdf_reader import extraer_texto_pdf  # función para extraer texto de PDFs
from drive_utils import listar_pdfs_drive, descargar_pdf_drive  # utilidades para Drive
from calendar_utils import crear_evento_calendar  # función para crear eventos en Calendar

from analyzer import (
    buscar_palabras_clave,
    buscar_fecha,
    calcular_fecha_limite,
)

# configuración básica de la página Streamlit
st.set_page_config(
    page_title="Gestor Inteligente de Documentos",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    # 📑 Gestor Inteligente de PDFs  
    ### Automatiza la detección de fechas y tareas desde documentos
    """
)

st.caption(
    "Analiza documentos desde Google Drive o tu equipo y prepara tareas automáticamente."
)

st.divider()  # separador visual

# proceso de callback / autenticación (si corresponde)
procesar_callback()
from auth_google import obtener_usuario  # importo aquí para evitar dependencias circulares

# si ya hay credenciales en sesión pero no info de usuario, la obtengo
if "credentials" in st.session_state and "user_info" not in st.session_state:
    st.session_state.user_info = obtener_usuario(
        st.session_state.credentials
    )

# diseño de dos columnas en la UI
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("📂 Fuentes de documentos")

    with st.container(border=True):
        st.markdown("### ☁️ Google Drive")
        st.caption("Carga y analiza PDFs desde tu cuenta de Google")

        # botón para listar PDFs desde Drive
        if st.button("📥 Cargar PDFs desde Drive", use_container_width=True):
            with st.spinner("Conectando con Google Drive..."):
                st.session_state.archivos_drive = listar_pdfs_drive(
                    st.session_state.credentials
                )

    with st.container(border=True):
        st.markdown("### 📎 Subir desde tu equipo")
        st.caption("Arrastra uno o varios documentos PDF")

        # uploader para archivos locales (acepta múltiples)
        pdfs = st.file_uploader(
            "Selecciona archivos PDF",
            type=["pdf"],
            accept_multiple_files=True,
            label_visibility="collapsed"
        )

        st.session_state.pdfs_locales = pdfs  # guardo los PDFs subidos en la sesión

with col2:
    st.subheader("🔍 Resultados del análisis")

    # sección para mostrar archivos obtenidos desde Drive
    if "archivos_drive" in st.session_state:
        archivos = st.session_state.archivos_drive

        if archivos:
            # selector múltiple para elegir archivos a analizar
            seleccionados = st.multiselect(
                "📄 Documentos desde Drive",
                archivos,
                format_func=lambda x: x["name"]
            )

            # botón para iniciar el análisis de los seleccionados
            if seleccionados and st.button("⚙️ Analizar documentos de Drive", use_container_width=True):
                for archivo in seleccionados:
                    with st.expander(f"📄 {archivo['name']}"):
                        # descargo el PDF desde Drive
                        pdf_bytes = descargar_pdf_drive(
                            st.session_state.credentials,
                            archivo["id"]
                        )

                        # extraigo texto del PDF
                        texto = extraer_texto_pdf(pdf_bytes)

                        # analizo palabras clave y fechas
                        palabras = buscar_palabras_clave(texto)
                        fecha_detectada = buscar_fecha(texto)
                        fecha_limite = calcular_fecha_limite(fecha_detectada)
                        
                        # botón para agendar el resultado en Calendar
                        if st.button("📅 Agendar en Google Calendar", key=f"calendar_drive_{archivo['id']}"):
                            crear_evento_calendar(
                                st.session_state.credentials,
                                titulo=f"Tarea: {archivo['name']}",
                                descripcion=f"Documento analizado: {archivo['name']}\n"
                                            f"Palabras clave: {', '.join(palabras) if palabras else 'Ninguna'}",
                                fecha_limite=fecha_limite,
                            )
                            st.success("Evento creado en tu Google Calendar")
                            
                            st.success("Documento analizado correctamente")

                        # muestro la fecha límite detectada
                        st.metric(
                            "📅 Fecha límite",
                            fecha_limite.strftime("%d/%m/%Y")
                        )

                        # muestro palabras clave encontradas
                        st.write("🔑 Palabras clave encontradas:")
                        st.write(palabras or "Ninguna")

                        # vista previa del texto extraído
                        st.text_area(
                            "Vista previa del texto",
                            texto[:3000],
                            height=180
                        )

    # sección para PDFs subidos localmente
    if "pdfs_locales" in st.session_state and st.session_state.pdfs_locales:
        st.divider()
        st.markdown("### 📎 PDFs locales")

        for pdf in st.session_state.pdfs_locales:
            with st.expander(f"📄 {pdf.name}"):
                texto = extraer_texto_pdf(pdf)  # extraigo texto del PDF local

                palabras = buscar_palabras_clave(texto)
                fecha_detectada = buscar_fecha(texto)
                fecha_limite = calcular_fecha_limite(fecha_detectada)
                if st.button("📅 Agendar en Google Calendar", key=f"calendar_local_{pdf.name}"):
                    crear_evento_calendar(
                        st.session_state.credentials,
                        titulo=f"Tarea: {pdf.name}",
                        descripcion=f"Documento analizado: {pdf.name}\n"
                                    f"Palabras clave: {', '.join(palabras) if palabras else 'Ninguna'}",
                        fecha_limite=fecha_limite,
                    )
                    st.success("Evento creado en tu Google Calendar")
                    

                st.metric(
                    "📅 Fecha límite",
                    fecha_limite.strftime("%d/%m/%Y")
                )

                st.write("🔑 Palabras clave:", palabras or "Ninguna")

                st.text_area(
                    "Texto (vista previa)",
                    texto[:3000],
                    height=180
                )



# ───────────────── LOGIN ─────────────────
if "credentials" not in st.session_state:
    st.warning("No has iniciado sesión")

    # botón para iniciar el flujo de autenticación
    if st.button("🔐 Iniciar sesión con Google"):
        url = iniciar_login()
        st.markdown(f"[👉 Autorizar aplicación]({url})")

    st.stop()  # detengo la ejecución hasta que el usuario inicie sesión

st.success("✅ Sesión iniciada correctamente")

# barra lateral con información del usuario y acciones
with st.sidebar:
    st.markdown("## 👤 Usuario conectado")

    usuario = st.session_state.get("user_info", {})
    st.write(f"**Email:** {usuario.get('email', 'No disponible')}")
    st.write(f"**Nombre:** {usuario.get('name', '')}")

    st.divider()

    st.markdown("## 📌 Acciones")
    st.markdown("✔ Analizar PDFs")
    st.markdown("⏳ Preparado para Calendar")

