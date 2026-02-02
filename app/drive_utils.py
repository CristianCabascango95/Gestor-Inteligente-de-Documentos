from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io


def listar_pdfs_drive(credentials):
    service = build("drive", "v3", credentials=credentials)

    results = service.files().list(
        q="mimeType='application/pdf'",
        fields="files(id, name)",
        pageSize=20
    ).execute()

    return results.get("files", [])


def descargar_pdf_drive(credentials, file_id):
    service = build("drive", "v3", credentials=credentials)

    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()

    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()

    fh.seek(0)
    return fh
