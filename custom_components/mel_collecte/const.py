"""Constantes de l'intégration MEL Collecte."""

DOMAIN = "mel_collecte"
DATA_COORDINATOR = "coordinator"

EVENT_COLLECTION_UPCOMING = "collection_upcoming"
DEFAULT_COLLECTION_OFFSET = 24

GEO_URL = "https://api.publidata.io/v2/geocoder"
SEARCH_URL = "https://api.publidata.io/v2/search"

DEFAULT_INSTANCE_ID = "876"

DEFAULT_UPDATE_INTERVAL = 7
DEFAULT_LOOKAHEAD_DAYS = 90
DEFAULT_VISIBLE_TYPES: list[str] = []

MAX_RETRIES = 3
RETRY_BASE_DELAY = 1
RETRY_MAX_DELAY = 30


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

GARBAGE_TYPES_LABELS_EN = {
    "omr": "Residual household waste",
    "dv": "Green waste",
    "cs": "Cardboard / bags",
    "enc": "Bulky items",
    "bio": "Biowaste",
    "verre": "Glass",
    "text": "Textiles",
    "deee": "Electronic waste",
    "pile": "Batteries",
    "emb": "Recyclable packaging",
}

ALERT_TYPE_LABELS = {
    "danger": "⚠️ Alerte",
    "warning": "⚡ Avertissement",
    "info": "ℹ️ Information",
}

ALERT_TYPE_LABELS_EN = {
    "danger": "⚠️ Alert",
    "warning": "⚡ Warning",
    "info": "ℹ️ Information",
}


def garbage_label(code: str, locale: str = "fr") -> str:
    """Retourne un libellé humain pour le type de déchet."""
    labels = GARBAGE_TYPES_LABELS_EN if locale == "en" else GARBAGE_TYPES_LABELS
    return labels.get(code.lower(), code.upper())


def alert_label(alert_type: str, locale: str = "fr") -> str:
    """Retourne un libellé humain pour le type d'alerte."""
    labels = ALERT_TYPE_LABELS_EN if locale == "en" else ALERT_TYPE_LABELS
    return labels.get(alert_type.lower(), alert_type.capitalize())


def get_locale(hass) -> str:
    """Retourne la langue courante de Home Assistant."""
    if hass is None:
        return "fr"
    return getattr(hass.config, "language", "fr") or "fr"
