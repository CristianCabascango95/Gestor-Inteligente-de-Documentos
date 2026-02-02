import streamlit as st
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build


# Asegúrate de que este nombre sea IGUAL al archivo que tienes en tu carpeta
CLIENT_SECRETS_FILE = "credentials.json" 
REDIRECT_URI = "http://localhost:8501"

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/userinfo.profile",
    "https://www.googleapis.com/auth/userinfo.email",
    "openid",
]

def iniciar_login():
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI,
    )
    
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url

def obtener_usuario(creds):
    service = build("oauth2", "v2", credentials=creds)
    user_info = service.userinfo().get().execute()
    return {
        "email": user_info.get("email"),
        "name": user_info.get("name"),
    }

def procesar_callback():
    # 1. Si ya estamos logueados, devolvemos las credenciales guardadas
    if "credentials" in st.session_state:
        return st.session_state["credentials"]

    # 2. Si no hay código en la URL, no hacemos nada
    if "code" not in st.query_params:
        return None

    code = st.query_params["code"]

    try:
        flow = Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI,
        )
        
        # 3. INTENTAMOS canjear el código (Aquí es donde fallaba antes)
        flow.fetch_token(code=code)
        
        # Si funciona, guardamos en sesión
        creds = flow.credentials
        st.session_state["credentials"] = creds
        
        # Y limpiamos la URL inmediatamente
        st.query_params.clear()
        
        return creds

    except Exception as e:
        # 4. SI FALLA (porque el código es viejo), NO crasheamos.
        # Simplemente limpiamos la URL para que el usuario pueda intentar de nuevo.
        st.warning("La sesión se actualizó. Por favor intenta conectar de nuevo si es necesario.")
        st.query_params.clear()
        return None
    