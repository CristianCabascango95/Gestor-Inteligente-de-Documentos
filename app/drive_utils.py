from googleapiclient.discovery import build  # constructor de cliente para Drive
from googleapiclient.http import MediaIoBaseDownload  # descarga por streams
import io  # para crear buffers en memoria


def listar_pdfs_drive(credentials):
    # creo el servicio usando las credenciales pasadas
    service = build("drive", "v3", credentials=credentials)

    # solicito a la API una lista de archivos PDF (id y nombre)
    results = service.files().list(
        q="mimeType='application/pdf'",
        fields="files(id, name)",
        pageSize=20
    ).execute()

    # devuelvo la lista de archivos o lista vacía
    return results.get("files", [])


def descargar_pdf_drive(credentials, file_id):
    # construyo el servicio de Drive
    service = build("drive", "v3", credentials=credentials)

    # creo la petición para obtener el contenido del archivo
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()  # buffer en memoria

    # uso MediaIoBaseDownload para descargar por chunks
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()  # descargo hasta completar

    fh.seek(0)  # vuelvo al inicio del buffer
    return fh  # devuelvo el buffer con el PDF
