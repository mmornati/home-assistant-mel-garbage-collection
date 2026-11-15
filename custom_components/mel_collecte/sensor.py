"""Capteurs de l'intégration MEL Collecte."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.util import dt as dt_util

from .facilities import facility_status, mobile_visits, next_mobile_visit
from .const import (
    DATA_COORDINATOR,
    DOMAIN,
    garbage_color,
    garbage_label,
    get_entry_language,
    ui_text,
)


async def async_setup_entry(hass: HomeAssistant, entry, async_add_entities):
    """Créer les capteurs."""
    coordinator = hass.data[DOMAIN][entry.entry_id][DATA_COORDINATOR]

    data = coordinator.data or {}
    collections = data.get("collections", [])

    visible_types = coordinator._visible_types

    entities: list[SensorEntity] = [
        MelCollecteNextSensor(coordinator, entry),
        MelCollecteNextCollectionDaysSensor(coordinator, entry),
        MelCollecteAlertSensor(coordinator, entry),
    ]

    facilities = data.get("facilities") or {}
    if facilities.get("recycling_center"):
        entities.append(MelCollecteRecyclingCenterSensor(coordinator, entry))
    if facilities.get("mobile"):
        entities.append(MelCollecteMobileRecyclingCenterSensor(coordinator, entry))

    seen_types: set[str] = set()
    for collection in collections:
        for garbage_type in collection.get("garbage_types", []):
            if garbage_type in seen_types:
                continue
            if visible_types and garbage_type not in visible_types:
                continue
            seen_types.add(garbage_type)
            entities.append(MelCollecteTypeSensor(coordinator, entry, garbage_type))
            entities.append(MelCollecteTypeDaysSensor(coordinator, entry, garbage_type))

    async_add_entities(entities)


class MelCollecteBaseSensor(SensorEntity):
    """Base commune aux capteurs."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:trash-can"

    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._entry = entry
        self._language = get_entry_language(entry)

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=ui_text("device_name", self._language),
            manufacturer="Publidata / MEL",
        )

    async def async_update(self):
        """Rien à récupérer : l'état est recalculé à partir des données déjà en mémoire.

        Home Assistant relit les capteurs toutes les 30 secondes ; les données,
        elles, sont rafraîchies par le coordonnateur à son propre rythme.
        """


class MelCollecteNextSensor(MelCollecteBaseSensor):
    """Capteur indiquant la prochaine collecte."""

    _attr_translation_key = "prochaine_collecte"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_next_collection"
        self._attr_name = ui_text("next_collection", self._language)

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
            "couleurs": [garbage_color(t) for t in event["garbage_types"]],
            "mode": event["collection_mode"],
            "debut": event["start"].isoformat(),
            "fin": event["end"].isoformat(),
        }

    def _next_event(self):
        now = dt_util.utcnow()
        data = self._coordinator.data or {}
        for event in data.get("events", []):
            if event["start"] >= now:
                return event
        return None


class MelCollecteNextCollectionDaysSensor(MelCollecteBaseSensor):
    """Capteur indiquant le nombre de jours avant la prochaine collecte."""

    _attr_translation_key = "jours_avant_prochaine_collecte"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_days_until_next_collection"
        self._attr_icon = "mdi:calendar-clock"
        self._attr_name = ui_text("days_until_next_collection", self._language)
        self._attr_native_unit_of_measurement = ui_text("days_unit", self._language)

    @property
    def native_value(self):
        event = self._next_event()
        if event:
            delta = event["start"].date() - dt_util.now().date()
            return delta.days
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        event = self._next_event()
        if not event:
            return {}
        return {
            "next_collection_date": event["start"].isoformat(),
            "next_collection_type": event.get(
                "garbage_types_friendly", ui_text("unknown", self._language)
            ),
        }

    def _next_event(self):
        now = dt_util.utcnow()
        data = self._coordinator.data or {}
        for event in data.get("events", []):
            if event["start"] >= now:
                return event
        return None


class MelCollecteTypeSensor(MelCollecteBaseSensor):
    """Un capteur par type de déchet."""

    def __init__(self, coordinator, entry, garbage_type: str):
        super().__init__(coordinator, entry)
        self._type = garbage_type
        self._attr_unique_id = f"{entry.entry_id}_type_{garbage_type}"
        self._attr_name = ui_text(
            "type_collection",
            self._language,
            label=garbage_label(garbage_type, self._language),
        )

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
            "couleur": garbage_color(self._type),
            "debut": event["start"].isoformat(),
            "fin": event["end"].isoformat(),
        }

    def _next_event_for_type(self):
        now = dt_util.utcnow()
        data = self._coordinator.data or {}
        for event in data.get("events", []):
            if event["start"] >= now and self._type in event["garbage_types"]:
                return event
        return None


class MelCollecteTypeDaysSensor(MelCollecteBaseSensor):
    """Capteur indiquant le nombre de jours avant la prochaine collecte d'un type spécifique."""

    def __init__(self, coordinator, entry, garbage_type: str):
        super().__init__(coordinator, entry)
        self._type = garbage_type
        self._attr_unique_id = f"{entry.entry_id}_type_{garbage_type}_days"
        self._attr_name = ui_text(
            "type_collection_in",
            self._language,
            label=garbage_label(garbage_type, self._language),
        )
        self._attr_native_unit_of_measurement = ui_text("days_unit", self._language)
        self._attr_icon = "mdi:calendar-clock"

    @property
    def native_value(self):
        event = self._next_event_for_type()
        if event:
            delta = event["start"].date() - dt_util.now().date()
            return delta.days
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        event = self._next_event_for_type()
        if not event:
            return {}
        return {
            "prochaine_collecte": event["start"].isoformat(),
            "type": self._type,
            "type_libelle": garbage_label(self._type, self._language),
            "couleur": garbage_color(self._type),
        }

    def _next_event_for_type(self):
        now = dt_util.utcnow()
        data = self._coordinator.data or {}
        for event in data.get("events", []):
            if event["start"] >= now and self._type in event["garbage_types"]:
                return event
        return None


class MelCollecteAlertSensor(MelCollecteBaseSensor):
    """Capteur pour les alertes du service de collecte."""

    _attr_translation_key = "alertes_collecte"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_alerts"
        self._attr_name = ui_text("collection_alerts", self._language)
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


class MelCollecteRecyclingCenterSensor(MelCollecteBaseSensor):
    """Déchèterie la plus proche de l'adresse, avec son état d'ouverture."""

    _attr_translation_key = "decheterie_la_plus_proche"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_nearest_recycling_center"
        self._attr_icon = "mdi:recycle-variant"
        self._attr_name = ui_text("nearest_recycling_center", self._language)

    def _places(self) -> list[dict[str, Any]]:
        data = self._coordinator.data or {}
        return (data.get("facilities") or {}).get("recycling_center") or []

    @property
    def native_value(self):
        places = self._places()
        return places[0]["name"] if places else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        places = self._places()
        if not places:
            return {}
        now = dt_util.now()
        nearest = places[0]
        status = facility_status(nearest, now)
        return {
            "adresse": nearest.get("address"),
            "distance_km": nearest.get("distance_km"),
            "ouverte": status["open"],
            "horaires_du_jour": status["today"],
            "fermeture": status["closes_at"],
            "prochaine_ouverture": status["next_open"],
            "horaires": nearest.get("opening_hours_text"),
            "latitude": nearest.get("lat"),
            "longitude": nearest.get("lon"),
            "decheteries": [
                {
                    "nom": place["name"],
                    "adresse": place.get("address"),
                    "distance_km": place.get("distance_km"),
                    "ouverte": facility_status(place, now)["open"],
                }
                for place in places[:5]
            ],
        }


class MelCollecteMobileRecyclingCenterSensor(MelCollecteBaseSensor):
    """Prochain passage d'une déchèterie mobile près de l'adresse."""

    _attr_translation_key = "prochaine_decheterie_mobile"

    def __init__(self, coordinator, entry):
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_next_mobile_recycling_center"
        self._attr_icon = "mdi:truck-cargo-container"
        self._attr_name = ui_text("next_mobile_recycling_center", self._language)

    def _places(self) -> list[dict[str, Any]]:
        data = self._coordinator.data or {}
        return (data.get("facilities") or {}).get("mobile") or []

    def _visit(self):
        # les trois plus proches : au-delà, ce n'est plus « près de chez vous »
        return next_mobile_visit(self._places()[:3], dt_util.now())

    @property
    def native_value(self):
        visit = self._visit()
        return visit[1].isoformat() if visit else None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        visit = self._visit()
        if not visit:
            return {}
        place, start, end = visit
        return {
            "nom": place["name"],
            "adresse": place.get("address"),
            "distance_km": place.get("distance_km"),
            "debut": start.isoformat(),
            "fin": end.isoformat(),
            "horaires": place.get("opening_hours_text"),
            "latitude": place.get("lat"),
            "longitude": place.get("lon"),
            # tous les sites des environs : une automatisation peut ainsi ne
            # retenir que ceux d'une commune
            "passages": [
                {
                    "nom": site["name"],
                    "adresse": site.get("address"),
                    "distance_km": site.get("distance_km"),
                    "debut": site_start.isoformat(),
                    "fin": site_end.isoformat(),
                }
                for site, site_start, site_end in mobile_visits(
                    self._places(), dt_util.now()
                )
            ],
        }
