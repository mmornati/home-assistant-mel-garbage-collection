"""Initialisation de l'intégration MEL Collecte."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType
from homeassistant.util import dt as dt_util
import voluptuous as vol

try:  # pragma: no cover - fallback pour exécution hors HA (tests)
    from homeassistant.helpers import aiohttp_client
except ImportError:  # pragma: no cover

    class _DummySession:  # type: ignore
        """Session factice pour les tests."""

    class aiohttp_client:  # type: ignore
        @staticmethod
        def async_get_clientsession(hass: HomeAssistant) -> _DummySession:
            return _DummySession()


from .api import MelCollecteAPI
from .const import (
    DATA_COORDINATOR,
    DEFAULT_LOOKAHEAD_DAYS,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VISIBLE_TYPES,
    DOMAIN,
    EVENT_COLLECTION_UPCOMING,
)
from .coordinator import MelCollecteCoordinator

PLATFORMS: list[str] = ["calendar", "sensor"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Configuration via configuration.yaml (non utilisée)."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Créer l'intégration à partir d'une entrée de configuration."""
    hass.data.setdefault(DOMAIN, {})

    session = aiohttp_client.async_get_clientsession(hass)
    api = MelCollecteAPI(session)

    options = entry.options or {}
    update_interval_days = options.get("update_interval", DEFAULT_UPDATE_INTERVAL)
    lookahead_days = options.get("lookahead_days", DEFAULT_LOOKAHEAD_DAYS)
    visible_types = options.get("visible_types", DEFAULT_VISIBLE_TYPES)

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address=entry.data["address"],
        instance_id=entry.data["instance_id"],
        lat=entry.data.get("lat"),
        lon=entry.data.get("lon"),
        update_interval_days=update_interval_days,
        lookahead_days=lookahead_days,
        visible_types=visible_types if visible_types else None,
    )
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = {DATA_COORDINATOR: coordinator}

    async def _async_fire_events() -> None:
        if not coordinator.data:
            return

        now = dt_util.utcnow()
        for event in coordinator.data.get("events", []):
            start = event["start"]
            time_until = start - now
            hours_until = time_until.total_seconds() / 3600

            if 0 <= hours_until <= coordinator.collection_offset_hours:
                event_key = (event["collection_id"], start.isoformat())
                if event_key not in coordinator.fired_events:
                    coordinator.fired_events.add(event_key)

                    payload = {
                        "entry_id": entry.entry_id,
                        "address": entry.data.get("address"),
                        "collection_id": event["collection_id"],
                        "collection_name": event.get("name"),
                        "garbage_types": event["garbage_types"],
                        "garbage_types_friendly": event["garbage_types_friendly"],
                        "start": start.isoformat(),
                        "end": event["end"].isoformat(),
                        "days_until": time_until.days,
                        "hours_until": int(hours_until),
                    }
                    hass.bus.async_fire(
                        f"{DOMAIN}.{EVENT_COLLECTION_UPCOMING}", payload
                    )

    entry.async_on_unload(
        coordinator.async_add_listener(
            lambda: hass.async_create_task(_async_fire_events())
        )
    )

    async def async_handle_refresh_service(call):
        """Force refresh of all or specific entries."""
        entry_id = call.data.get("entry_id")
        if entry_id:
            if entry_id in hass.data.get(DOMAIN, {}):
                coord = hass.data[DOMAIN][entry_id].get(DATA_COORDINATOR)
                if coord:
                    await coord.async_request_refresh()
        else:
            for instance_id in hass.data.get(DOMAIN, {}):
                coord = hass.data[DOMAIN][instance_id].get(DATA_COORDINATOR)
                if coord:
                    await coord.async_request_refresh()

    hass.services.async_register(
        DOMAIN,
        "force_refresh",
        async_handle_refresh_service,
        schema=vol.Schema({vol.Optional("entry_id"): str}),
    )

    async def async_handle_set_offset_service(call):
        """Configure event lead time (offset)."""
        entry_id = call.data.get("entry_id")
        hours_before = call.data.get("hours_before", 24)
        if entry_id:
            if entry_id in hass.data.get(DOMAIN, {}):
                coord = hass.data[DOMAIN][entry_id].get(DATA_COORDINATOR)
                if coord:
                    coord.collection_offset_hours = hours_before
        else:
            for instance_id in hass.data.get(DOMAIN, {}):
                coord = hass.data[DOMAIN][instance_id].get(DATA_COORDINATOR)
                if coord:
                    coord.collection_offset_hours = hours_before

    hass.services.async_register(
        DOMAIN,
        "set_collection_offset",
        async_handle_set_offset_service,
        schema=vol.Schema(
            {
                vol.Optional("entry_id"): str,
                vol.Required("hours_before"): vol.Coerce(int),
            }
        ),
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Retirer l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
        if not hass.data[DOMAIN]:
            hass.services.async_remove(DOMAIN, "force_refresh")
            hass.services.async_remove(DOMAIN, "set_collection_offset")
    return unload_ok
