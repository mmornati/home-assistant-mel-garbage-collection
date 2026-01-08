"""Capteurs de l'intégration MEL Collecte."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import DATA_COORDINATOR, DOMAIN, garbage_label


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Créer les capteurs."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    entities: list[SensorEntity] = [
        MelCollecteNextSensor(coordinator, entry),
        MelCollecteAlertSensor(coordinator, entry),
    ]

    seen_types: set[str] = set()
    for collection in coordinator.data["collections"]:
        for garbage_type in collection.get("garbage_types", []):
            if garbage_type in seen_types:
                continue
            seen_types.add(garbage_type)
            entities.append(MelCollecteTypeSensor(coordinator, entry, garbage_type))

    async_add_entities(entities)


class MelCollecteBaseSensor(SensorEntity):
    """Base commune aux capteurs."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:trash-can"

    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Collectes MEL",
            manufacturer="Publidata / MEL",
        )

    async def async_update(self):
        await self._coordinator.async_request_refresh()


class MelCollecteNextSensor(MelCollecteBaseSensor):
    """Capteur indiquant la prochaine collecte."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_next_collection"
        self._attr_name = "Prochaine collecte"

    @property
    def native_value(self):
        event = self._next_event()
        if event:
            return event["start"].isoformat()
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        event = self._next_event()
        if not event:
            return {}
        return {
            "collection_id": event["collection_id"],
            "types": event["garbage_types"],
            "types_friendly": event.get("garbage_types_friendly"),
            "mode": event["collection_mode"],
            "debut": event["start"].isoformat(),
            "fin": event["end"].isoformat(),
        }

    def _next_event(self):
        now = dt_util.utcnow()
        for event in self._coordinator.data["events"]:
            if event["start"] >= now:
                return event
        return None


class MelCollecteTypeSensor(MelCollecteBaseSensor):
    """Un capteur par type de déchet."""

    def __init__(self, coordinator, entry, garbage_type: str):
        super().__init__(coordinator, entry)
        self._type = garbage_type
        self._attr_unique_id = f"{entry.entry_id}_type_{garbage_type}"
        self._label = garbage_label(garbage_type)
        self._attr_name = f"Collecte {self._label}"

    @property
    def native_value(self):
        event = self._next_event_for_type()
        if event:
            return event["start"].isoformat()
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        event = self._next_event_for_type()
        if not event:
            return {}
        return {
            "collection_id": event["collection_id"],
            "mode": event["collection_mode"],
            "types": event["garbage_types"],
            "types_friendly": event.get("garbage_types_friendly"),
            "debut": event["start"].isoformat(),
            "fin": event["end"].isoformat(),
        }

    def _next_event_for_type(self):
        now = dt_util.utcnow()
        for event in self._coordinator.data["events"]:
            if event["start"] >= now and self._type in event["garbage_types"]:
                return event
        return None


class MelCollecteAlertSensor(MelCollecteBaseSensor):
    """Capteur pour les alertes du service de collecte."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_alerts"
        self._attr_name = "Alertes collecte"
        self._attr_icon = "mdi:alert-circle"

    @property
    def native_value(self):
        """Retourne le nombre d'alertes actives."""
        alerts = self._coordinator.data.get("alerts", [])
        return len(alerts)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Retourne les détails des alertes."""
        alerts = self._coordinator.data.get("alerts", [])
        if not alerts:
            return {"alerts": []}

        return {
            "alerts": [
                {
                    "id": alert.get("id"),
                    "name": alert.get("name"),
                    "type": alert.get("alert_type"),
                    "type_friendly": alert.get("alert_type_friendly"),
                    "message": alert.get("blurb"),
                    "published_at": alert.get("published_at"),
                    "end_at": alert.get("end_at"),
                }
                for alert in alerts
            ],
            "last_alert_name": alerts[0].get("name") if alerts else None,
            "last_alert_type": alerts[0].get("alert_type") if alerts else None,
            "last_alert_message": alerts[0].get("blurb") if alerts else None,
        }

