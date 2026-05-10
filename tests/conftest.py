"""Stubs légers pour les modules Home Assistant lors des tests unitaires."""

from __future__ import annotations

import sys
import types
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional


def _ensure_module(name: str) -> types.ModuleType:
    module = sys.modules.get(name)
    if module is None:
        module = types.ModuleType(name)
        sys.modules[name] = module
    return module


# Crée les modules racine
ha = _ensure_module("homeassistant")

# ----- homeassistant.const ------------------------------------------------
const_module = _ensure_module("homeassistant.const")
const_module.CONF_ADDRESS = "address"
ha.const = const_module

# ----- homeassistant.core -------------------------------------------------
core = _ensure_module("homeassistant.core")


def callback(func):
    """Simple callback decorator stub."""
    return func


class HomeAssistant:
    """Stub minimal de HomeAssistant utilisé dans les tests."""

    def __init__(self, loop: Any | None = None) -> None:
        self.loop = loop


core.callback = callback
core.HomeAssistant = HomeAssistant
ha.core = core

# ----- homeassistant.config_entries ---------------------------------------
config_entries = _ensure_module("homeassistant.config_entries")


class ConfigEntry:  # pragma: no cover - stub simple
    """Stub pour ConfigEntry."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class ConfigFlowMeta(type):
    """Metaclass that accepts domain keyword."""

    def __new__(mcs, name, bases, namespace, domain=None, **kwargs):
        return super().__new__(mcs, name, bases, namespace)

    def __init__(cls, name, bases, namespace, domain=None, **kwargs):
        super().__init__(name, bases, namespace)


class _ConfigFlowBase(metaclass=ConfigFlowMeta, domain=None):
    VERSION = 1

    def __init__(self, hass=None, **kwargs):
        self.hass = hass

    async def async_step_user(self, user_input=None):
        return None

    def async_show_form(self, **kwargs):
        return {"type": "form", **kwargs}

    def async_create_entry(self, **kwargs):
        return {"type": "create_entry", **kwargs}

    def async_abort(self, **kwargs):
        return {"type": "abort", **kwargs}

    async def async_set_unique_id(self, unique_id):
        pass

    def _abort_if_unique_id_configured(self):
        pass

    @staticmethod
    def async_get_options_flow(config_entry):
        return None


ConfigFlow = _ConfigFlowBase


config_entries.ConfigEntry = ConfigEntry
config_entries.ConfigFlow = ConfigFlow
config_entries.OptionsFlowWithConfigEntry = type("OptionsFlowWithConfigEntry", (), {})
ha.config_entries = config_entries

# ----- homeassistant.helpers.entity ---------------------------------------
helpers = _ensure_module("homeassistant.helpers")
entity_module = _ensure_module("homeassistant.helpers.entity")


@dataclass
class DeviceInfo:
    identifiers: set[tuple[str, str]]
    name: Optional[str] = None
    manufacturer: Optional[str] = None
    configuration_url: Optional[str] = None


class Entity:
    """Version simplifiée de la classe Entity."""

    _attr_name: Optional[str] = None
    _attr_unique_id: Optional[str] = None
    _attr_has_entity_name: bool = False
    _attr_icon: Optional[str] = None

    @property
    def name(self) -> Optional[str]:
        return getattr(self, "_attr_name", None)

    @property
    def unique_id(self) -> Optional[str]:
        return getattr(self, "_attr_unique_id", None)

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {}


entity_module.Entity = Entity
entity_module.DeviceInfo = DeviceInfo
helpers.entity = entity_module

# aiohttp_client stub
aiohttp_client_module = _ensure_module("homeassistant.helpers.aiohttp_client")


class DummyClientSession:
    """Objet factice représentant une session aiohttp."""


def async_get_clientsession(hass: HomeAssistant) -> DummyClientSession:
    return DummyClientSession()


aiohttp_client_module.async_get_clientsession = async_get_clientsession
helpers.aiohttp_client = aiohttp_client_module

# typing stub
typing_module = _ensure_module("homeassistant.helpers.typing")


class ConfigType(dict):  # pragma: no cover - simple alias
    pass


typing_module.ConfigType = ConfigType
helpers.typing = typing_module

# config_validation stub
config_validation_module = _ensure_module("homeassistant.helpers.config_validation")


def config_entry_only_config_schema(
    domain: str,
):  # pragma: no cover - simple passthrough
    def _schema(_config: Optional[dict] = None):
        return {}

    return _schema


config_validation_module.config_entry_only_config_schema = (
    config_entry_only_config_schema
)
helpers.config_validation = config_validation_module

# ----- homeassistant.components.sensor ------------------------------------
components = _ensure_module("homeassistant.components")
sensor_module = _ensure_module("homeassistant.components.sensor")


class SensorEntity(Entity):
    """Stub minimal de SensorEntity."""

    @property
    def native_value(self):
        return None


sensor_module.SensorEntity = SensorEntity
components.sensor = sensor_module
ha.components = components

# ----- homeassistant.components.calendar ----------------------------------
calendar_module = _ensure_module("homeassistant.components.calendar")


@dataclass
class CalendarEvent:
    summary: str
    start: datetime
    end: datetime
    description: str | None = None


class CalendarEntity(Entity):
    """Stub minimal de CalendarEntity."""

    def __init__(self) -> None:
        super().__init__()

    async def async_get_events(self, hass, start, end):
        return []

    @property
    def event(self) -> CalendarEvent | None:
        return None


calendar_module.CalendarEntity = CalendarEntity
calendar_module.CalendarEvent = CalendarEvent
components.calendar = calendar_module

# ----- homeassistant.helpers.update_coordinator --------------------------
update_coordinator = _ensure_module("homeassistant.helpers.update_coordinator")


class UpdateFailed(Exception):
    """Exception déclenchée en cas d'échec de mise à jour."""


class DataUpdateCoordinator:
    """Stub très simplifié de DataUpdateCoordinator."""

    def __class_getitem__(
        cls, _item
    ):  # pragma: no cover - support pour annotations génériques
        return cls

    def __init__(self, hass, logger, name: str, update_interval=None) -> None:
        self.hass = hass
        self.logger = logger
        self.name = name
        self.update_interval = update_interval

    async def async_request_refresh(self):
        return None


update_coordinator.UpdateFailed = UpdateFailed
update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
helpers.update_coordinator = update_coordinator

# ----- homeassistant.util.dt ----------------------------------------------
dt_module = _ensure_module("homeassistant.util.dt")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


dt_module.utcnow = utcnow
dt_module.as_utc = as_utc

ha.helpers = helpers
ha.util = types.ModuleType("homeassistant.util")
ha.util.dt = dt_module
sys.modules["homeassistant.util"] = ha.util
sys.modules["homeassistant.util.dt"] = dt_module

# ----- aiohttp stub -------------------------------------------------------
aiohttp_module = types.ModuleType("aiohttp")


class ClientError(Exception):
    """Simulates aiohttp.ClientError."""


class ClientSession:  # pragma: no cover - simple stub
    """ClientSession factice pour éviter d'installer aiohttp."""


class ClientConnectorError(ClientError):
    """Simulates aiohttp.ClientConnectorError."""

    def __init__(self, *args, **kwargs):
        super().__init__(str(args[0]) if args else "connection error")


class ServerDisconnectedError(ClientError):
    """Simulates aiohttp.ServerDisconnectedError."""


aiohttp_module.ClientError = ClientError
aiohttp_module.ClientConnectorError = ClientConnectorError
aiohttp_module.ServerDisconnectedError = ServerDisconnectedError
aiohttp_module.ClientSession = ClientSession
sys.modules["aiohttp"] = aiohttp_module

# ----- async_timeout stub -------------------------------------------------
async_timeout_module = types.ModuleType("async_timeout")


class timeout:  # pragma: no cover - simple context manager
    def __init__(self, *_args, **_kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


async_timeout_module.timeout = timeout
sys.modules["async_timeout"] = async_timeout_module
