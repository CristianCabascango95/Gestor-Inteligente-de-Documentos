from googleapiclient.discovery import build  # constructor de clientes para Google APIs
from datetime import datetime, timedelta  # utilidades de fecha y duración
from zoneinfo import ZoneInfo  # zona horaria estándar


def crear_evento_calendar(
    creds,
    titulo,
    descripcion,
    fecha_limite,
):
    # construyo el servicio de Calendar con las credenciales proporcionadas
    service = build("calendar", "v3", credentials=creds)

    # inicio del evento: combino la fecha límite con la hora mínima del día
    zona = ZoneInfo("America/Guayaquil")
    fecha_base = fecha_limite.date() if isinstance(fecha_limite, datetime) else fecha_limite
    inicio = datetime.combine(fecha_base, datetime.min.time()).replace(tzinfo=zona)
    # duración por defecto: 1 hora
    fin = inicio + timedelta(hours=1)

    # estructura del evento que se enviará a la API de Calendar
    evento = {
        "summary": titulo,  # título del evento
        "description": descripcion,  # descripción detallada
        "start": {
            "dateTime": inicio.isoformat(),  # inicio en ISO8601
            "timeZone": "America/Guayaquil",
        },
        "end": {
            "dateTime": fin.isoformat(),  # fin en ISO8601
            "timeZone": "America/Guayaquil",
        },
    }

    # inserto el evento en el calendario principal (primary)
    evento_creado = service.events().insert(
        calendarId="primary",
        body=evento
    ).execute()

    # devuelvo el enlace web al evento recién creado
    return evento_creado.get("htmlLink")


def obtener_eventos_calendar(creds, dias=30):
    """Obtiene los próximos eventos del calendario dentro de los próximos `dias` días."""
    service = build("calendar", "v3", credentials=creds)
    
    # ahora y fecha límite
    ahora = datetime.utcnow().isoformat() + 'Z'
    fecha_limite = (datetime.utcnow() + timedelta(days=dias)).isoformat() + 'Z'
    
    try:
        # solicito los eventos del calendario en el rango de fechas
        eventos = service.events().list(
            calendarId='primary',
            timeMin=ahora,
            timeMax=fecha_limite,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        
        return eventos.get('items', [])
    except Exception as e:
        print(f"Error al obtener eventos: {e}")
        return []
