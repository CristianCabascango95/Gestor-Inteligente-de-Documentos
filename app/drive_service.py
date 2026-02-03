from googleapiclient.discovery import build  # para construir el cliente Drive
from googleapiclient.http import MediaIoBaseDownload  # utilidad para descargar archivos
from io import BytesIO  # buffer en memoria para almacenar el PDF descargado


def listar_pdfs(creds, limite=10):
    # creo el servicio de Drive usando las credenciales
    service = build("drive", "v3", credentials=creds)

    # pido a la API una lista de archivos con mimeType PDF
    resultados = service.files().list(
        q="mimeType='application/pdf'",
        pageSize=limite,
        fields="files(id, name)"
    ).execute()

    # devuelvo la lista de archivos (o lista vacía si no hay resultados)
    return resultados.get("files", [])


def descargar_pdf(creds, file_id):
    # construyo el servicio de Drive con las credenciales
    service = build("drive", "v3", credentials=creds)
    # creo la petición para obtener el contenido binario del archivo
    request = service.files().get_media(fileId=file_id)

    buffer = BytesIO()  # buffer en memoria donde se escribirá el PDF
    downloader = MediaIoBaseDownload(buffer, request)  # objeto que gestiona la descarga

    done = False
    while not done:  # descargo por chunks hasta completar
        _, done = downloader.next_chunk()

    buffer.seek(0)  # posiciono el cursor al inicio del buffer
    return buffer  # devuelvo el buffer con los bytes del PDF
