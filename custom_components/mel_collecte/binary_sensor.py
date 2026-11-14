"""Capteurs binaires de l'intégration MEL Collecte."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .const import DATA_COORDINATOR, DOMAIN, get_entry_language, ui_text
from .facilities import facility_status


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Créer le capteur d'ouverture de la déchèterie la plus proche."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]
    facilities = (coordinator.data or {}).get("facilities") or {}
    if facilities.get("recycling_center"):
        async_add_entities([MelCollecteRecyclingCenterOpenSensor(coordinator, entry)])


class MelCollecteRecyclingCenterOpenSensor(BinarySensorEntity):
    """Indique si la déchèterie la plus proche est ouverte en ce moment."""

    _attr_has_entity_name = True
    _attr_translation_key = "decheterie_ouverte"

    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._entry = entry
        self._language = get_entry_language(entry)
        self._attr_unique_id = f"{entry.entry_id}_recycling_center_open"
        self._attr_name = ui_text("recycling_center_open", self._language)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=ui_text("device_name", self._language),
            manufacturer="Publidata / MEL",
        )

    def _nearest(self) -> dict[str, Any] | None:
        data = self._coordinator.data or {}
        places = (data.get("facilities") or {}).get("recycling_center") or []
        return places[0] if places else None

    @property
    def icon(self) -> str:
        return "mdi:gate-open" if self.is_on else "mdi:gate"

    @property
    def is_on(self) -> bool | None:
        nearest = self._nearest()
        if not nearest:
            return None
        return facility_status(nearest, dt_util.now())["open"]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        nearest = self._nearest()
        if not nearest:
            return {}
        status = facility_status(nearest, dt_util.now())
        return {
            "nom": nearest["name"],
            "distance_km": nearest.get("distance_km"),
            "horaires_du_jour": status["today"],
            "fermeture": status["closes_at"],
            "prochaine_ouverture": status["next_open"],
        }

    async def async_update(self):
        """Rien à récupérer : l'état dépend seulement de l'heure."""
