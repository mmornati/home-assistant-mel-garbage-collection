"""DataUpdateCoordinator pour les données de collecte."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import MelCollecteAPI
from .const import LOOKAHEAD_DAYS, UPDATE_INTERVAL_DAYS, alert_label, garbage_label
from .parser import parse_schedule

LOGGER = logging.getLogger(__name__)


class MelCollecteCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordonne les requêtes vers l'API Publidata."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MelCollecteAPI,
        *,
        address: str,
        instance_id: str,
        lat: float | None,
        lon: float | None,
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name="MEL Collecte Coordinator",
            update_interval=timedelta(days=UPDATE_INTERVAL_DAYS),
        )
        self.api = api
        self.address = address
        self.instance_id = instance_id
        self.lat = lat
        self.lon = lon
        self._address_payload: dict[str, Any] | None = None

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            if not self._address_payload:
                self._address_payload = await self.api.geocode_address(self.address)
                if not self._address_payload:
                    raise UpdateFailed("Adresse introuvable dans l'API Publidata")

            coordinates = self._address_payload["geometry"]["coordinates"]
            fetched_lat = self.lat if self.lat is not None else coordinates[1]
            fetched_lon = self.lon if self.lon is not None else coordinates[0]
            address_id = self._address_payload["properties"]["id"]

            collections = await self.api.fetch_waste_collections(
                instance_id=self.instance_id,
                address_id=address_id,
                lat=fetched_lat,
                lon=fetched_lon,
            )

            # Fetch alerts from the service
            alerts = await self.api.fetch_alerts(
                instance_id=self.instance_id,
                address_id=address_id,
            )
        except Exception as err:
            LOGGER.error("Erreur lors de la récupération des collectes: %s", err)
            raise UpdateFailed(err) from err

        now = dt_util.utcnow()
        horizon = now + timedelta(days=LOOKAHEAD_DAYS)
        events: list[dict[str, Any]] = []
        parsed_collections: list[dict[str, Any]] = []

        for collection in collections:
            schedules = collection.get("schedules", [])
            occurrences = []
            for schedule in schedules:
                opening_hours = schedule.get("opening_hours")
                if not opening_hours:
                    continue
                occurrences.extend(parse_schedule(opening_hours, now, horizon))

            friendly_types = [
                garbage_label(code)
                for code in collection.get("metas", {}).get("garbage_types", [])
            ]

            parsed_collections.append(
                {
                    "id": collection.get("id"),
                    "name": collection.get("name"),
                    "garbage_types": collection.get("metas", {}).get(
                        "garbage_types", []
                    ),
                    "garbage_types_friendly": friendly_types,
                    "collection_mode": collection.get("metas", {}).get(
                        "collection_mode"
                    ),
                    "accepted_waste": collection.get("metas", {}).get(
                        "accepted_waste", []
                    ),
                    "rejected_waste": collection.get("metas", {}).get(
                        "rejected_waste", []
                    ),
                    "occurrences": occurrences,
                }
            )

            events.extend(
                {
                    "collection_id": collection.get("id"),
                    "garbage_types": collection.get("metas", {}).get(
                        "garbage_types", []
                    ),
                    "garbage_types_friendly": friendly_types,
                    "collection_mode": collection.get("metas", {}).get(
                        "collection_mode"
                    ),
                    "start": dt_util.as_utc(occurrence["start"]),
                    "end": dt_util.as_utc(occurrence["end"]),
                    "name": collection.get("name"),
                }
                for occurrence in occurrences
            )

        events.sort(key=lambda item: item["start"])

        # Parse alerts
        parsed_alerts = [
            {
                "id": alert.get("id"),
                "name": alert.get("name"),
                "alert_type": alert.get("alert_type"),
                "alert_type_friendly": alert_label(alert.get("alert_type", "")),
                "blurb": alert.get("blurb"),
                "start_at": alert.get("start_at"),
                "end_at": alert.get("end_at"),
                "published_at": alert.get("published_at"),
            }
            for alert in alerts
        ]

        return {
            "address": self._address_payload,
            "collections": parsed_collections,
            "events": events,
            "alerts": parsed_alerts,
            "fetched_at": now.isoformat(),
        }
