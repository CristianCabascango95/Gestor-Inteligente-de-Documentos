from googleapiclient.discovery import build
from datetime import datetime, timedelta


def crear_evento_calendar(
    creds,
    titulo,
    descripcion,
    fecha_limite,
):
    service = build("calendar", "v3", credentials=creds)

    inicio = datetime.combine(fecha_limite, datetime.min.time())
    fin = inicio + timedelta(hours=1)

    evento = {
        "summary": titulo,
        "description": descripcion,
        "start": {
            "dateTime": inicio.isoformat(),
            "timeZone": "America/Guayaquil",
        },
        "end": {
            "dateTime": fin.isoformat(),
            "timeZone": "America/Guayaquil",
        },
    }

    evento_creado = service.events().insert(
        calendarId="primary",
        body=evento
    ).execute()

    return evento_creado.get("htmlLink")
