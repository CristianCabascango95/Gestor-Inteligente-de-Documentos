import re
from datetime import datetime, timedelta

PALABRAS_CLAVE = [
    "hasta",
    "departamento de",
    "jefe de departamento",
    "docente",
    "para",
    "entregar",
    "fecha límite",
    "plazo",
    "entrega",
    "asunto"
]


def buscar_palabras_clave(texto: str):
    texto_lower = texto.lower()
    encontradas = []

    for palabra in PALABRAS_CLAVE:
        if palabra in texto_lower:
            encontradas.append(palabra)

    return encontradas


def buscar_fecha(texto: str):
    """
    Busca fechas tipo:
    12/03/2026
    12-03-2026
    12 de marzo de 2026
    """

    patrones = [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{4}",
        r"\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4}",
    ]

    for patron in patrones:
        match = re.search(patron, texto.lower())
        if match:
            fecha_texto = match.group()
            try:
                return convertir_fecha(fecha_texto)
            except Exception:
                pass

    return None


def convertir_fecha(fecha_str: str):
    fecha_str = fecha_str.strip()

    if "/" in fecha_str or "-" in fecha_str:
        for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(fecha_str, fmt)
            except ValueError:
                continue

    meses = {
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }

    partes = fecha_str.split()
    dia = int(partes[0])
    mes = meses.get(partes[2])
    anio = int(partes[4])

    return datetime(anio, mes, dia)


def calcular_fecha_limite(fecha_detectada):
    if fecha_detectada:
        return fecha_detectada

    return datetime.now() + timedelta(days=2)
