import streamlit as st  # interfaz web ligera usada en la aplicación
from google_auth_oauthlib.flow import Flow  # flujo OAuth2 para Google
from googleapiclient.discovery import build  # constructor de servicios de Google API
import pickle
import os
from pathlib import Path


# Nombre del archivo JSON con las credenciales de OAuth (debe existir en el proyecto)
CLIENT_SECRETS_FILE = "credentials.json"
# URI de redirección usada por Streamlit en local
REDIRECT_URI = "http://localhost:8501"
# Archivo para guardar credenciales persistentes
CREDENTIALS_FILE = ".streamlit/credentials.pkl"

SCOPES = [  # permisos solicitados a Google
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]


def guardar_credenciales(creds):
    """Guarda las credenciales en un archivo pickle para persistencia."""
    try:
        # Crea el directorio si no existe
        Path(CREDENTIALS_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(CREDENTIALS_FILE, 'wb') as f:
            pickle.dump(creds, f)
    except Exception as e:
        print(f"Error al guardar credenciales: {e}")


def cargar_credenciales():
    """Carga las credenciales del archivo pickle si existen."""
    try:
        if os.path.exists(CREDENTIALS_FILE):
            with open(CREDENTIALS_FILE, 'rb') as f:
                return pickle.load(f)
    except Exception as e:
        print(f"Error al cargar credenciales: {e}")
    return None


def eliminar_credenciales():
    """Elimina el archivo de credenciales guardadas."""
    try:
        if os.path.exists(CREDENTIALS_FILE):
            os.remove(CREDENTIALS_FILE)
    except Exception as e:
        print(f"Error al eliminar credenciales: {e}")


def iniciar_login():
    # creo el flujo OAuth a partir del archivo de secretos
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )

    # genero la URL de autorización que el usuario debe visitar
    auth_url, _ = flow.authorization_url(
        access_type="offline",  # solicitar refresh token
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url  # devuelvo la URL para redirigir al usuario


def obtener_usuario(creds):
    # construyo el servicio oauth2 para obtener información del usuario
    service = build("oauth2", "v2", credentials=creds)
    user_info = service.userinfo().get().execute()  # solicito los datos del usuario
    return {
        "email": user_info.get("email"),  # correo del usuario
        "name": user_info.get("name"),  # nombre del usuario
    }


def procesar_callback():
    # 1. Si ya tenemos credenciales en sesión, devolverlas
    if "credentials" in st.session_state:
        return st.session_state["credentials"]

    # 2. Si no hay código en la URL, no hay callback que procesar
    if "code" not in st.query_params:
        return None

    code = st.query_params["code"]  # extraigo el código de la URL

    try:
        # recreo el flujo para intercambiar el código por credenciales
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )

        # intento canjear el código por tokens (access + refresh)
        flow.fetch_token(code=code)

        # si todo fue bien, obtengo las credenciales
        creds = flow.credentials
        st.session_state["credentials"] = creds  # las guardo en la sesión
        guardar_credenciales(creds)  # guardo en archivo para persistencia

        # limpio los parámetros de la URL para evitar reintentos automáticos
        st.query_params.clear()

        return creds  # devuelvo las credenciales obtenidas

    except Exception as e:
        # Si algo falló (p. ej. código expirado), no lanzo excepción crítica
        # aviso al usuario y limpio la URL para permitir reintentar
        st.warning("La sesión se actualizó. Por favor intenta conectar de nuevo si es necesario.")
        st.query_params.clear()
        return None
    