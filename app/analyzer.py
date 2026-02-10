import re  # módulo para operaciones con expresiones regulares
from datetime import datetime, timedelta  # importo tipos de fecha y duración

PALABRAS_CLAVE = [  # lista de palabras/frases relevantes a buscar en documentos
    "De mi consideración",
    "Ing. Edwin Oswaldo Chasiquiza Molina, Mgtr", # PRIORIDAD: busca responsable/encargado
    "encargado",  
    "hasta",
    "departamento de",
    "jefe de departamento",
    "jefe de laboratorio",
    "docente",
    "para",
    "entregar",
    "fecha límite",
    "plazo",
    "entrega",
    "asunto",
    "presentar"
    
    
]


def buscar_encargado(texto: str):
    """Busca al encargado/responsable en el texto (prioridad máxima)."""
    texto_lower = texto.lower()
    
    # Patrones para buscar encargado
    patrones_encargado = [
        r"encargado[^\n]*",  # encargado seguido de info
        r"jefe[\s\w]*\([^)]*encargado[^)]*\)",  # jefe (...Encargado)
        r"([A-Z][a-záéíóú]+[\s\w.,]*)\s+\(encargado\)",  # Nombre (Encargado)
    ]
    
    for patron in patrones_encargado:
        match = re.search(patron, texto, re.IGNORECASE)
        if match:
            return match.group().strip()
    
    return None


def buscar_palabras_clave(texto: str):
    texto_lower = texto.lower()  # convierto todo el texto a minúsculas
    encontradas = []  # lista donde guardaré las palabras encontradas
    
    # Primero busco al encargado y lo agrego con prioridad
    encargado = buscar_encargado(texto)
    if encargado:
        encontradas.append(f"Encargado: {encargado}")

    for palabra in PALABRAS_CLAVE:  # itero cada palabra clave
        if palabra in texto_lower:  # si la palabra aparece en el texto
            encontradas.append(palabra)  # la añado a la lista de encontradas

    return encontradas  # devuelvo la lista de palabras encontradas


def buscar_fecha(texto: str):
    """
    Busca fechas en el texto en distintos formatos:
    - 12/03/2026
    - 12-03-2026
    - 12 de marzo de 2026
    """

    patrones = [  # patrones regex para detectar formatos de fecha
        r"\d{1,2}[/-]\d{1,2}[/-]\d{4}",  # dd/mm/yyyy o dd-mm-yyyy
        r"\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4}",  # '12 de marzo de 2026'
    ]

    for patron in patrones:  # pruebo cada patrón contra el texto
        match = re.search(patron, texto.lower())  # busco la primera coincidencia
        if match:  # si encontré algo
            fecha_texto = match.group()  # extraigo la cadena que coincide
            try:
                return convertir_fecha(fecha_texto)  # intento convertirla a datetime
            except Exception:
                pass  # si falla la conversión sigo probando otros patrones

    return None  # si no se encontró ninguna fecha, devuelvo None


def _extraer_fechas(texto: str):
    """Extrae todas las fechas con su posicion en el texto."""
    fechas = []
    patrones = [
        r"\d{1,2}[/-]\d{1,2}[/-]\d{4}",
        r"\d{1,2}\s+de\s+[a-zA-Z]+\s+de\s+\d{4}",
    ]
    for patron in patrones:
        for match in re.finditer(patron, texto.lower()):
            try:
                fecha = convertir_fecha(match.group())
                fechas.append((fecha, match.start()))
            except Exception:
                continue
    return fechas


def buscar_fecha_limite_doc(texto: str):
    """Busca la fecha limite usando palabras clave (hasta, plazo, fecha limite)."""
    texto_lower = texto.lower()
    fechas = _extraer_fechas(texto)
    if not fechas:
        return None

    patrones_clave = [
        r"hasta",
        r"fecha\s*l[ií]mite",
        r"plazo",
        r"entregar",
        r"entrega",
        r"a\s+mas\s+tardar",
        r"antes\s+del",
    ]

    indices_clave = []
    for patron in patrones_clave:
        for match in re.finditer(patron, texto_lower):
            indices_clave.append(match.start())

    if indices_clave:
        # Busco la primera fecha despues de una palabra clave cercana.
        mejor = None
        mejor_dist = None
        for fecha, idx in fechas:
            for idx_clave in indices_clave:
                if idx >= idx_clave:
                    dist = idx - idx_clave
                    if mejor is None or dist < mejor_dist:
                        mejor = fecha
                        mejor_dist = dist
        if mejor:
            return mejor

    # Si no hay palabras clave, uso la fecha mas lejana (posible fecha limite)
    return max(f for f, _ in fechas)


def buscar_asunto(texto: str):
    """Extrae el asunto desde una linea tipo 'Asunto: ...' si existe."""
    match = re.search(r"^\s*asunto\s*[:\-]\s*(.+)$", texto, re.IGNORECASE | re.MULTILINE)
    if match:
        return match.group(1).strip()
    return None


def detectar_accion(texto: str):
    """Detecta la accion principal para titular el evento."""
    texto_lower = texto.lower()
    if "entregar" in texto_lower or "entrega" in texto_lower:
        return "Entregar"
    if "presentar" in texto_lower:
        return "Presentar"
    return "Tarea"


def convertir_fecha(fecha_str: str):
    fecha_str = fecha_str.strip()  # elimino espacios al inicio/final

    if "/" in fecha_str or "-" in fecha_str:  # formato numérico con / o -
        for fmt in ("%d/%m/%Y", "%d-%m-%Y"):  # posibles formatos
            try:
                return datetime.strptime(fecha_str, fmt)  # intento parsear
            except ValueError:
                continue  # si falla, pruebo el siguiente formato

    meses = {  # mapeo nombres de meses a su número
        "enero": 1, "febrero": 2, "marzo": 3, "abril": 4,
        "mayo": 5, "junio": 6, "julio": 7, "agosto": 8,
        "septiembre": 9, "octubre": 10, "noviembre": 11, "diciembre": 12,
    }

    partes = fecha_str.split()
    dia = int(partes[0])
    mes = meses.get(partes[2])
    anio = int(partes[4])

    return datetime(anio, mes, dia)  # construyo y devuelvo el objeto datetime


def calcular_fecha_limite(fecha_detectada):
    if fecha_detectada:  # si ya detectamos una fecha, la usamos como límite
        return fecha_detectada

    return datetime.now() + timedelta(days=2)  # si no, uso hoy + 2 días como predeterminado


def calcular_fecha_agenda(fecha_detectada):
    """Calcula la fecha de agenda (2 dias antes de la fecha limite)."""
    if fecha_detectada:
        return fecha_detectada - timedelta(days=2)
    return datetime.now() + timedelta(days=2)
