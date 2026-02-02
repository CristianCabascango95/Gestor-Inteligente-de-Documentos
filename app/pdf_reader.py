from pypdf import PdfReader


def extraer_texto_pdf(file):
    reader = PdfReader(file)
    texto = ""

    for page in reader.pages:
        if page.extract_text():
            texto += page.extract_text() + "\n"

    return texto
