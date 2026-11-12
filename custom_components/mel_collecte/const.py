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

CONF_LANGUAGE = "language"
DEFAULT_LANGUAGE = "fr"
SUPPORTED_LANGUAGES = ["fr", "en"]
LANGUAGE_CHOICES = {"fr": "Français", "en": "English"}

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


def get_entry_language(entry) -> str:
    """Retourne la langue choisie pour une entrée (options > data > défaut)."""
    for source in (getattr(entry, "options", None), getattr(entry, "data", None)):
        if source and source.get(CONF_LANGUAGE) in SUPPORTED_LANGUAGES:
            return source[CONF_LANGUAGE]
    return DEFAULT_LANGUAGE


UI_TEXTS: dict[str, dict[str, str]] = {
    "fr": {
        "device_name": "Collectes MEL",
        "next_collection": "Prochaine collecte",
        "days_until_next_collection": "Jours avant prochaine collecte",
        "collection_alerts": "Alertes collecte",
        "calendar": "Collectes des déchets",
        "type_collection": "Collecte {label}",
        "type_collection_in": "Collecte {label} dans",
        "days_unit": "jours",
        "unknown": "Inconnu",
    },
    "en": {
        "device_name": "MEL Collections",
        "next_collection": "Next collection",
        "days_until_next_collection": "Days until next collection",
        "collection_alerts": "Collection alerts",
        "calendar": "Waste collections",
        "type_collection": "{label} collection",
        "type_collection_in": "{label} collection in",
        "days_unit": "days",
        "unknown": "Unknown",
    },
}


def ui_text(key: str, locale: str = DEFAULT_LANGUAGE, **kwargs: str) -> str:
    """Retourne un texte d'interface dans la langue demandée."""
    texts = UI_TEXTS.get(locale, UI_TEXTS[DEFAULT_LANGUAGE])
    return texts[key].format(**kwargs)
