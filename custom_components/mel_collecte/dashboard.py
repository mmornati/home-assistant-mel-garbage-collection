"""Cartes de tableau de bord fournies avec l'intégration.

Les cartes sont des composants web en JavaScript simple, dans ``frontend/`` :
aucune étape de compilation, aucune carte tierce à installer. Home Assistant
sert le fichier et le charge dans chaque navigateur ; les cartes apparaissent
alors dans le sélecteur « Ajouter une carte ».

Les cartes ne devinent pas les identifiants d'entités (ils dépendent de la
langue et l'utilisateur peut les renommer). Elles interrogent la commande
websocket ``mel_collecte/dashboard``, qui renvoie tout ce qu'il faut afficher.
"""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    garbage_color,
    garbage_label,
    get_entry_language,
)
from .facilities import with_status

_LOGGER = logging.getLogger(__name__)

FRONTEND_URL = f"/{DOMAIN}_frontend"
CARDS_FILE = "mel-collecte-cards.js"
FRONTEND_DIR = Path(__file__).parent / "frontend"
_REGISTERED = f"{DOMAIN}_dashboard_registered"

# rôle -> suffixe de l'identifiant unique de l'entité
ENTITY_ROLES = {
    "next": "next_collection",
    "days": "days_until_next_collection",
    "alerts": "alerts",
    "calendar": "calendar",
    "recycling_center": "nearest_recycling_center",
    "recycling_center_open": "recycling_center_open",
    "mobile": "next_mobile_recycling_center",
}


def entry_payload(
    entry_id: str,
    title: str,
    address: str | None,
    language: str,
    data: dict[str, Any],
    now: datetime,
    entities: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Tout ce que les cartes affichent pour une adresse."""
    events = []
    types: dict[str, dict[str, str]] = {}
    for event in data.get("events", []):
        if event["end"] < now:
            continue
        codes = event["garbage_types"]
        for code in codes:
            types.setdefault(
                code,
                {"label": garbage_label(code, language), "color": garbage_color(code)},
            )
        events.append(
            {
                "start": event["start"].isoformat(),
                "end": event["end"].isoformat(),
                "types": codes,
                "mode": event.get("collection_mode"),
            }
        )

    facilities = {
        kind: [with_status(place, now) for place in places]
        for kind, places in (data.get("facilities") or {}).items()
    }

    return {
        "entry_id": entry_id,
        "title": title,
        "address": address,
        "language": language,
        "home": data.get("home"),
        "now": now.isoformat(),
        "updated": data.get("last_update_success") or data.get("fetched_at"),
        "events": events,
        "types": types,
        "alerts": data.get("alerts", []),
        "guide": data.get("guide", []),
        "contacts": data.get("contacts", {}),
        "facilities": facilities,
        "entities": entities or {},
    }


def dashboard_payload(hass) -> dict[str, Any]:
    """Réponse de la commande websocket : une section par adresse configurée."""
    # importés ici : inutiles tant qu'aucune carte n'est affichée
    from homeassistant.helpers import entity_registry as er
    from homeassistant.util import dt as dt_util

    registry = er.async_get(hass)
    by_unique_id = {
        item.unique_id: item.entity_id
        for item in registry.entities.values()
        if item.platform == DOMAIN and item.disabled_by is None
    }
    now = dt_util.now()

    entries = []
    for entry in hass.config_entries.async_entries(DOMAIN):
        stored = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        coordinator = stored.get(DATA_COORDINATOR) if stored else None
        if coordinator is None or not coordinator.data:
            continue
        entities = {
            role: by_unique_id[f"{entry.entry_id}_{suffix}"]
            for role, suffix in ENTITY_ROLES.items()
            if f"{entry.entry_id}_{suffix}" in by_unique_id
        }
        entries.append(
            entry_payload(
                entry.entry_id,
                entry.title,
                entry.data.get("address"),
                get_entry_language(entry),
                coordinator.data,
                now,
                entities,
            )
        )
    return {"entries": entries}


async def async_register_dashboard(hass, version: str) -> None:
    """Sert les cartes, les charge dans les navigateurs et déclare la commande websocket."""
    if hass.data.get(_REGISTERED):
        return
    hass.data[_REGISTERED] = True

    import voluptuous as vol
    from homeassistant.components import websocket_api
    from homeassistant.core import callback

    @websocket_api.websocket_command({vol.Required("type"): f"{DOMAIN}/dashboard"})
    @callback
    def ws_dashboard(hass, connection, msg) -> None:
        connection.send_result(msg["id"], dashboard_payload(hass))

    websocket_api.async_register_command(hass, ws_dashboard)

    if "frontend" not in hass.config.components or getattr(hass, "http", None) is None:
        _LOGGER.debug("Pas d'interface web : les cartes ne sont pas servies")
        return
    from homeassistant.components.frontend import add_extra_js_url
    from homeassistant.components.http import StaticPathConfig

    await hass.http.async_register_static_paths(
        [StaticPathConfig(FRONTEND_URL, str(FRONTEND_DIR), True)]
    )
    # le numéro de version force les navigateurs à recharger le fichier après une mise à jour
    add_extra_js_url(hass, f"{FRONTEND_URL}/{CARDS_FILE}?v={version}")
