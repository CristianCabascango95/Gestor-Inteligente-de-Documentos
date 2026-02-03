import streamlit as st  # interfaz web para la app
from datetime import datetime  # para parsear fechas
from auth_google import iniciar_login, procesar_callback, cargar_credenciales  # funciones de autenticación
from pdf_reader import extraer_texto_pdf  # función para extraer texto de PDFs
from drive_utils import listar_pdfs_drive, descargar_pdf_drive  # utilidades para Drive
from calendar_utils import crear_evento_calendar, obtener_eventos_calendar  # función para crear eventos en Calendar

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

# Si acabamos de iniciar sesión (posible popup), notificamos al opener y cerramos la ventana
if st.session_state.get("just_logged_in"):
    # Insertamos JS que marca localStorage y notifica al opener, luego cierra la ventana (popup)
    st.components.v1.html(
        """
        <script>
        try {
            localStorage.setItem('oauth_done', '1');
            if (window.opener) {
                window.opener.postMessage({oauth_done: 1}, '*');
            }
            // Cerrar la ventana popup
            window.close();
        } catch (e) { }
        </script>
        """,
        height=0,
        unsafe_allow_html=True,
    )
    # limpiamos la señal para evitar repeticiones
    st.session_state["just_logged_in"] = False

# Aseguro que la clave `credentials` exista en la sesión (inicialmente None)
st.session_state.setdefault("credentials", None)

# Si no hay credenciales en sesión, intento cargarlas de archivo
if not st.session_state.get("credentials"):
    creds_guardadas = cargar_credenciales()
    if creds_guardadas:
        st.session_state.credentials = creds_guardadas

# si ya hay credenciales en sesión pero no info de usuario, la obtengo
if st.session_state.get("credentials") and "user_info" not in st.session_state:
    st.session_state.user_info = obtener_usuario(st.session_state.get("credentials"))

# diseño de dos columnas en la UI
col1, col2 = st.columns(2, gap="large")

with col1:
    st.subheader("📂 Fuentes de documentos")

    with st.container(border=True):
        st.markdown("### ☁️ Google Drive")
        st.caption("Carga y analiza PDFs desde tu cuenta de Google")

        # botón para listar PDFs desde Drive
        if st.button("📥 Cargar PDFs desde Drive", use_container_width=True):
            if not st.session_state.credentials:
                st.warning("Debes iniciar sesión para acceder a Google Drive.")
            else:
                with st.spinner("Conectando con Google Drive..."):
                    st.session_state.archivos_drive = listar_pdfs_drive(
                        st.session_state.get("credentials")
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
    
    # Sección de calendario
    with st.container(border=True):
        st.markdown("### 📅 Google Calendar")
        st.caption("Eventos agendados y preparados")
        
        if st.session_state.get("credentials"):
            st.success("✅ Conectado a Google Calendar")
            
            # Obtengo los eventos del calendario
            eventos = obtener_eventos_calendar(st.session_state.get("credentials"), dias=30)
            
            if eventos:
                st.markdown("#### 📌 Próximos eventos (30 días):")
                
                # Muestro los eventos en un formato visual
                for evento in eventos:
                    inicio = evento.get('start', {}).get('dateTime', evento.get('start', {}).get('date', 'N/A'))
                    titulo = evento.get('summary', 'Sin título')
                    descripcion = evento.get('description', '')[:100]  # primeros 100 caracteres
                    
                    # Parseo la fecha
                    try:
                        if 'T' in inicio:
                            fecha_obj = datetime.fromisoformat(inicio.replace('Z', '+00:00'))
                            fecha_formateada = fecha_obj.strftime("%d/%m/%Y %H:%M")
                        else:
                            fecha_formateada = inicio
                    except:
                        fecha_formateada = inicio
                    
                    # Muestro el evento en un contenedor expandible
                    with st.expander(f"📋 {titulo} - {fecha_formateada}"):
                        st.write(f"**Fecha:** {fecha_formateada}")
                        if descripcion:
                            st.write(f"**Detalles:** {descripcion}")
                        # Enlace al evento en Google Calendar
                        enlace = evento.get('htmlLink', '')
                        if enlace:
                            st.markdown(f"[🔗 Abrir en Google Calendar]({enlace})")
            else:
                st.info("📭 No hay eventos próximos en los próximos 30 días")
        else:
            st.warning("⏳ Inicia sesión para ver Google Calendar")

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
                        # descargo el PDF desde Drive (verifico credenciales)
                        if not st.session_state.get("credentials"):
                            st.warning("Debes iniciar sesión para descargar archivos de Drive.")
                            continue
                        pdf_bytes = descargar_pdf_drive(
                            st.session_state.get("credentials"),
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
                            if not st.session_state.get("credentials"):
                                st.warning("Inicia sesión para crear eventos en Google Calendar.")
                            else:
                                crear_evento_calendar(
                                    st.session_state.get("credentials"),
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
                    if not st.session_state.get("credentials"):
                        st.warning("Inicia sesión para crear eventos en Google Calendar.")
                    else:
                        crear_evento_calendar(
                            st.session_state.get("credentials"),
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
if not st.session_state.get("credentials"):
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
    
    # Estado del calendario
    if st.session_state.get("credentials"):
        st.markdown("✅ Google Calendar conectado")
        
        # Botón para cerrar sesión
        if st.button("🔓 Cerrar sesión", use_container_width=True):
            from auth_google import eliminar_credenciales
            eliminar_credenciales()
            st.session_state.credentials = None
            st.session_state.user_info = None
            st.rerun()
    else:
        st.markdown("⏳ Google Calendar no configurado")

