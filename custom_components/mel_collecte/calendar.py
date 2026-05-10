"""Entité calendrier pour les collectes MEL."""

from __future__ import annotations

from datetime import datetime
from typing import List

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import DATA_COORDINATOR, DOMAIN, garbage_label


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
    _attr_translation_key = "collectes_des_dechets"

    def __init__(self, coordinator, entry, visible_types: list[str] | None = None):
        self._coordinator = coordinator
        self._entry = entry
        self._visible_types = visible_types or []
        self._attr_unique_id = f"{entry.entry_id}_calendar"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="MEL Collections",
            manufacturer="Publidata / MEL",
            configuration_url="https://lillemetropole.fr/",
        )

    def _translate_garbage_types(
        self, garbage_types: List[str], locale: str
    ) -> List[str]:
        """Traduit les types de déchets en utilisant les codes."""
        return [garbage_label(gt, locale) for gt in garbage_types]

    def _format_event_summary(self, evt, locale: str) -> str:
        """Formate le résumé de l'événement avec les types traduits."""
        codes = evt.get("garbage_types") or []
        if codes:
            translated_codes = self._translate_garbage_types(codes, locale)
            return ", ".join(translated_codes)
        return evt.get("name", "")

    def _format_event_description(self, evt, locale: str) -> str:
        """Formate la description de l'événement avec les types traduits."""
        codes = evt.get("garbage_types") or []
        if codes:
            translated_codes = self._translate_garbage_types(codes, locale)
            return f"{evt['name']} • {', '.join(translated_codes)}"
        return evt.get("name", "")

    def _get_locale(self) -> str:
        """Retourne la langue courante de Home Assistant ou 'fr' par défaut."""
        hass = getattr(self, "hass", None)
        if hass is None:
            return "fr"
        return getattr(hass.config, "language", "fr") or "fr"

    @property
    def event(self) -> CalendarEvent | None:
        now = dt_util.utcnow()
        data = self._coordinator.data or {}
        events = data.get("events", [])
        locale = self._get_locale()
        for evt in events:
            if evt["start"] < now:
                continue
            if self._visible_types and not any(
                t in self._visible_types for t in evt.get("garbage_types", [])
            ):
                continue
            return CalendarEvent(
                summary=self._format_event_summary(evt, locale),
                start=evt["start"],
                end=evt["end"],
                description=self._format_event_description(evt, locale),
            )
        return None

    async def async_get_events(
        self, hass: HomeAssistant, start_date: datetime, end_date: datetime
    ) -> List[CalendarEvent]:
        events = []
        start_date = dt_util.as_utc(start_date)
        end_date = dt_util.as_utc(end_date)
        data = self._coordinator.data or {}
        locale = self._get_locale()
        for evt in data.get("events", []):
            if evt["end"] < start_date or evt["start"] > end_date:
                continue
            if self._visible_types and not any(
                t in self._visible_types for t in evt.get("garbage_types", [])
            ):
                continue
            events.append(
                CalendarEvent(
                    summary=self._format_event_summary(evt, locale),
                    start=evt["start"],
                    end=evt["end"],
                    description=self._format_event_description(evt, locale),
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
