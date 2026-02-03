from googleapiclient.discovery import build  # constructor de clientes para Google APIs
from datetime import datetime, timedelta  # utilidades de fecha y duración


def crear_evento_calendar(
    creds,
    titulo,
    descripcion,
    fecha_limite,
):
    # construyo el servicio de Calendar con las credenciales proporcionadas
    service = build("calendar", "v3", credentials=creds)

    # inicio del evento: combino la fecha límite con la hora mínima del día
    inicio = datetime.combine(fecha_limite, datetime.min.time())
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
