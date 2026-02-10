from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime

try:
    import spacy
except Exception:
    spacy = None

from dateutil import parser
from analyzer import convertir_fecha

_NLP = None


def _get_nlp():
    global _NLP
    if _NLP is not None:
        return _NLP
    if spacy is None:
        return None
    try:
        _NLP = spacy.load("es_core_news_sm")
    except OSError:
        return None
    return _NLP


def _parse_date(text: str) -> Optional[datetime]:
    cleaned = text.strip().lower()
    try:
        return convertir_fecha(cleaned)
    except Exception:
        pass

    try:
        return parser.parse(cleaned, dayfirst=True, fuzzy=True)
    except Exception:
        return None


def extraer_entidades_ia(texto: str) -> Dict[str, Any]:
    nlp = _get_nlp()
    if nlp is None:
        return {
            "error": "missing_model",
            "responsable": None,
            "fecha_limite": None,
        }

    doc = nlp(texto)
    responsable = None
    fecha_limite = None

    for ent in doc.ents:
        if responsable is None and ent.label_ in ("PER", "PERSON"):
            responsable = ent.text.strip()
        if fecha_limite is None and ent.label_ == "DATE":
            fecha_limite = _parse_date(ent.text)
        if responsable and fecha_limite:
            break

    return {
        "responsable": responsable,
        "fecha_limite": fecha_limite,
    }
