"""Entité calendrier pour les collectes MEL."""

from __future__ import annotations

from datetime import datetime
from typing import List

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import DATA_COORDINATOR, DOMAIN


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Créer l'entité calendrier."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    async_add_entities([MelCollecteCalendar(coordinator, entry)])


class MelCollecteCalendar(CalendarEntity):
    """Calendrier regroupant l'ensemble des collectes."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_calendar"
        self._attr_name = "Collectes des déchets"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Collectes MEL",
            manufacturer="Publidata / MEL",
            configuration_url="https://lillemetropole.fr/",
        )

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.utcnow()
        for evt in self._coordinator.data["events"]:
            if evt["start"] >= now:
                friendly = evt.get("garbage_types_friendly") or evt.get("garbage_types") or []
                return CalendarEvent(
                    summary=", ".join(friendly) or evt["name"],
                    start=evt["start"],
                    end=evt["end"],
                    description=f"{evt['name']} • {', '.join(friendly)}",
                )
        return None

    async def async_get_events(self, hass: HomeAssistant, start_date: datetime, end_date: datetime) -> List[CalendarEvent]:
        events = []
        start_date = dt_util.as_utc(start_date)
        end_date = dt_util.as_utc(end_date)
        for evt in self._coordinator.data["events"]:
            if evt["end"] < start_date or evt["start"] > end_date:
                continue
            friendly = evt.get("garbage_types_friendly") or evt.get("garbage_types") or []
            events.append(
                CalendarEvent(
                    summary=", ".join(friendly) or evt["name"],
                    start=evt["start"],
                    end=evt["end"],
                    description=f"{evt['name']} • {', '.join(friendly)}",
                )
            )
        return events

    @property
    def extra_state_attributes(self):
        return {
            "derniere_mise_a_jour": self._coordinator.data.get("fetched_at"),
            "nombre_evenements": len(self._coordinator.data["events"]),
        }

    async def async_update(self):
        await self._coordinator.async_request_refresh()

