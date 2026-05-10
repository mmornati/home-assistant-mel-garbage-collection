"""Constantes de l'intégration MEL Collecte."""

DOMAIN = "mel_collecte"
DATA_COORDINATOR = "coordinator"

GEO_URL = "https://api.publidata.io/v2/geocoder"
SEARCH_URL = "https://api.publidata.io/v2/search"

DEFAULT_INSTANCE_ID = "876"  # Métropole Européenne de Lille

DEFAULT_UPDATE_INTERVAL = 7
DEFAULT_LOOKAHEAD_DAYS = 90
DEFAULT_VISIBLE_TYPES: list[str] = []

# Retry configuration
MAX_RETRIES = 3
RETRY_BASE_DELAY = 1  # seconds
RETRY_MAX_DELAY = 30  # seconds


class TransientError(Exception):
    """Erreur transitoire (réseau, timeout, limite de débit) — réessayable."""


class PermanentError(Exception):
    """Erreur permanente (adresse invalide, clé API incorrecte) — ne pas réessayer."""


GARBAGE_TYPES_LABELS = {
    "omr": "Ordures ménagères résiduelles",
    "dv": "Déchets verts",
    "cs": "Cartons / sacs",
    "enc": "Encombrants",
    "bio": "Biodéchets",
    "verre": "Verre",
    "text": "Textiles",
    "deee": "Déchets électroniques",
    "pile": "Piles et batteries",
    "emb": "Emballages recyclables",
}

ALERT_TYPE_LABELS = {
    "danger": "⚠️ Alerte",
    "warning": "⚡ Avertissement",
    "info": "ℹ️ Information",
}


def garbage_label(code: str) -> str:
    """Retourne un libellé humain pour le type de déchet."""
    return GARBAGE_TYPES_LABELS.get(code.lower(), code.upper())


def alert_label(alert_type: str) -> str:
    """Retourne un libellé humain pour le type d'alerte."""
    return ALERT_TYPE_LABELS.get(alert_type.lower(), alert_type.capitalize())
