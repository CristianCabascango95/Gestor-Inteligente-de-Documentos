from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO

def listar_pdfs(creds, limite=10):
    service = build("drive", "v3", credentials=creds)

    resultados = service.files().list(
        q="mimeType='application/pdf'",
        pageSize=limite,
        fields="files(id, name)"
    ).execute()

    return resultados.get("files", [])


def descargar_pdf(creds, file_id):
    service = build("drive", "v3", credentials=creds)
    request = service.files().get_media(fileId=file_id)

    buffer = BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    buffer.seek(0)
    return buffer
