from pypdf import PdfReader  # lector de PDFs


def extraer_texto_pdf(file):
    # creo un lector de PDF a partir del archivo/puntero pasado
    reader = PdfReader(file)
    texto = ""  # acumulador de texto extraído

    for page in reader.pages:  # itero por cada página del PDF
        if page.extract_text():  # si la página tiene texto extraíble
            texto += page.extract_text() + "\n"  # lo añado al acumulador

    return texto  # devuelvo el texto completo extraído
