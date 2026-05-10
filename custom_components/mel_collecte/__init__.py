"""Initialisation de l'intégration MEL Collecte."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.typing import ConfigType

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

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Retirer l'intégration."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
