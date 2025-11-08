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
from .const import DATA_COORDINATOR, DOMAIN
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

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address=entry.data["address"],
        instance_id=entry.data["instance_id"],
        lat=entry.data.get("lat"),
        lon=entry.data.get("lon"),
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

