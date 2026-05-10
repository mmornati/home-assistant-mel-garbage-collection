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
    options = entry.options or {}
    visible_types = options.get("visible_types") or []
    async_add_entities([MelCollecteCalendar(coordinator, entry, visible_types)])


class MelCollecteCalendar(CalendarEntity):
    """Calendrier regroupant l'ensemble des collectes."""

    _attr_has_entity_name = True
    _attr_has_time = True

    def __init__(self, coordinator, entry, visible_types: list[str] | None = None):
        self._coordinator = coordinator
        self._entry = entry
        self._visible_types = visible_types or []
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
        data = self._coordinator.data or {}
        events = data.get("events", [])
        for evt in events:
            if evt["start"] < now:
                continue
            if self._visible_types and not any(
                t in self._visible_types for t in evt.get("garbage_types", [])
            ):
                continue
            friendly = (
                evt.get("garbage_types_friendly") or evt.get("garbage_types") or []
            )
            return CalendarEvent(
                summary=", ".join(friendly) or evt["name"],
                start=evt["start"],
                end=evt["end"],
                description=f"{evt['name']} • {', '.join(friendly)}",
            )
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        events = []
        start_date = dt_util.as_utc(start_date)
        end_date = dt_util.as_utc(end_date)
        data = self._coordinator.data or {}
        for evt in data.get("events", []):
            if evt["end"] < start_date or evt["start"] > end_date:
                continue
            if self._visible_types and not any(
                t in self._visible_types for t in evt.get("garbage_types", [])
            ):
                continue
            friendly = (
                evt.get("garbage_types_friendly") or evt.get("garbage_types") or []
            )
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
        data = self._coordinator.data or {}
        return {
            "derniere_mise_a_jour": data.get("fetched_at"),
            "nombre_evenements": len(data.get("events", [])),
        }

    async def async_update(self):
        if self._coordinator.last_update_success:
            await self._coordinator.async_request_refresh()
