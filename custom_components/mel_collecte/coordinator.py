"""DataUpdateCoordinator pour les données de collecte."""

from __future__ import annotations

import logging
import re
from html import unescape
from datetime import datetime, timedelta, timezone
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from .api import MelCollecteAPI
from .const import (
    DROP_OFF_INSTANCE_ID,
    FACILITIES_INSTANCE_ID,
    DEFAULT_LOOKAHEAD_DAYS,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VISIBLE_TYPES,
    DEFAULT_COLLECTION_OFFSET,
    DEFAULT_LANGUAGE,
    alert_label,
    garbage_color,
    garbage_label,
)
from .facilities import (
    FACILITY_COMPOSTER,
    FACILITY_GLASS,
    FACILITY_MOBILE,
    FACILITY_RECYCLING_CENTER,
    normalize_facilities,
)
from .parser import parse_schedule

_TAG = re.compile(r"<[^>]+>")


def _plain_text(html: str | None) -> str:
    """Retire les balises des textes publiés par la MEL."""
    text = _TAG.sub(" ", html or "").replace("&nbsp;", " ")
    return " ".join(unescape(text).split())


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
        update_interval_days: int = DEFAULT_UPDATE_INTERVAL,
        lookahead_days: int = DEFAULT_LOOKAHEAD_DAYS,
        visible_types: list[str] | None = None,
        language: str = DEFAULT_LANGUAGE,
    ) -> None:
        super().__init__(
            hass,
            LOGGER,
            name="MEL Collecte Coordinator",
            update_interval=timedelta(days=update_interval_days),
        )
        self.api = api
        self.address = address
        self.instance_id = instance_id
        self.lat = lat
        self.lon = lon
        self._lookahead_days = lookahead_days
        self.language = language
        self._visible_types = (
            visible_types if visible_types is not None else DEFAULT_VISIBLE_TYPES
        )
        self._address_payload: dict[str, Any] | None = None
        self._last_update_success: datetime | None = None

        self._facilities: dict[str, list[dict[str, Any]]] = {}

        self.fired_events: set[tuple[str, str]] = set()
        self.collection_offset_hours = DEFAULT_COLLECTION_OFFSET

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            if not self._address_payload:
                self._address_payload = await self.api.geocode_address(self.address)
                if not self._address_payload:
                    raise UpdateFailed("Adresse introuvable dans l'API Publidata")

            geometry = self._address_payload.get("geometry", {})
            coordinates = geometry.get("coordinates")
            if (
                not coordinates
                or not isinstance(coordinates, list)
                or len(coordinates) < 2
            ):
                raise UpdateFailed("Coordonnées invalides dans la réponse géocodage")
            fetched_lat = self.lat if self.lat is not None else coordinates[1]
            fetched_lon = self.lon if self.lon is not None else coordinates[0]

            properties = self._address_payload.get("properties", {})
            address_id = properties.get("id")
            if not address_id:
                raise UpdateFailed("ID d'adresse manquant dans la réponse géocodage")

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
            LOGGER.warning(
                "Erreur lors de la récupération des collectes (le coordonnateur réessaiera) : %s",
                err,
            )
            raise UpdateFailed(err) from err

        facilities = await self._async_fetch_facilities(
            fetched_lat, fetched_lon, properties.get("postcode")
        )

        # la MEL publie des heures locales : les créneaux se calculent en heure
        # locale, puis sont convertis en UTC
        now = dt_util.now()
        horizon = now + timedelta(days=self._lookahead_days)
        events: list[dict[str, Any]] = []
        parsed_collections: list[dict[str, Any]] = []

        for collection in collections:
            collection_types = collection.get("metas", {}).get("garbage_types", [])
            if self._visible_types and all(
                t not in self._visible_types for t in collection_types
            ):
                continue

            schedules = collection.get("schedules", [])
            occurrences = []
            for schedule in schedules:
                opening_hours = schedule.get("opening_hours")
                if not opening_hours:
                    continue
                occurrences.extend(parse_schedule(opening_hours, now, horizon))

            friendly_types = [
                garbage_label(code, self.language) for code in collection_types
            ]

            parsed_collections.append(
                {
                    "id": collection.get("id"),
                    "name": collection.get("name"),
                    "garbage_types": collection_types,
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

            for occurrence in occurrences:
                event_types = collection_types
                if self._visible_types:
                    event_types = [t for t in event_types if t in self._visible_types]
                if not event_types:
                    continue

                friendly_event_types = [
                    garbage_label(code, self.language) for code in event_types
                ]
                events.append(
                    {
                        "collection_id": collection.get("id"),
                        "garbage_types": event_types,
                        "garbage_types_friendly": friendly_event_types,
                        "collection_mode": collection.get("metas", {}).get(
                            "collection_mode"
                        ),
                        "start": dt_util.as_utc(occurrence["start"]),
                        "end": dt_util.as_utc(occurrence["end"]),
                        "name": collection.get("name"),
                    }
                )

        events.sort(key=lambda item: item["start"])

        # Parse alerts
        parsed_alerts = [
            {
                "id": alert.get("id"),
                "name": alert.get("name"),
                "alert_type": alert.get("alert_type"),
                "alert_type_friendly": alert_label(
                    alert.get("alert_type", ""), self.language
                ),
                "blurb": alert.get("blurb"),
                "text": _plain_text(alert.get("blurb")),
                "start_at": alert.get("start_at"),
                "end_at": alert.get("end_at"),
                "published_at": alert.get("published_at"),
            }
            for alert in alerts
        ]

        self._last_update_success = datetime.now(timezone.utc)

        return {
            "address": self._address_payload,
            "collections": parsed_collections,
            "events": events,
            "alerts": parsed_alerts,
            "guide": self._build_guide(collections),
            "contacts": self._build_contacts(collections),
            "facilities": facilities,
            "home": {"lat": fetched_lat, "lon": fetched_lon},
            "fetched_at": now.isoformat(),
            "last_update_success": self._last_update_success.isoformat(),
        }

    async def _async_fetch_facilities(
        self, lat: float, lon: float, postcode: str | None
    ) -> dict[str, list[dict[str, Any]]]:
        """Déchèteries et points d'apport proches de l'adresse.

        Ces lieux complètent les collectes : une erreur ici ne doit pas faire
        échouer la mise à jour, on garde alors la dernière liste connue.
        """
        requests: list[tuple[str, int, str | None]] = [
            (FACILITIES_INSTANCE_ID, FACILITY_RECYCLING_CENTER, None),
            (FACILITIES_INSTANCE_ID, FACILITY_MOBILE, None),
            (FACILITIES_INSTANCE_ID, FACILITY_COMPOSTER, None),
        ]
        if postcode:
            # les bornes à verre se comptent par milliers : on se limite au code postal
            requests.append((DROP_OFF_INSTANCE_ID, FACILITY_GLASS, str(postcode)))

        raw: list[dict[str, Any]] = []
        try:
            for instance_id, facility_type, query in requests:
                raw.extend(
                    await self.api.fetch_facilities(instance_id, facility_type, query)
                )
        except Exception as err:  # pylint: disable=broad-except
            LOGGER.warning(
                "Déchèteries et points d'apport indisponibles (dernière liste conservée) : %s",
                err,
            )
            return self._facilities

        self._facilities = normalize_facilities(raw, lat, lon)
        return self._facilities

    def _build_guide(self, collections: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Consignes de tri par type de déchet (ce qui est accepté ou refusé)."""
        guide: dict[str, dict[str, Any]] = {}
        # les collectes de l'adresse (avec horaires) priment sur les fiches générales
        ordered = sorted(collections, key=lambda item: not item.get("schedules"))
        for collection in ordered:
            metas = collection.get("metas") or {}
            accepted = [text for text in metas.get("accepted_waste") or [] if text]
            rejected = [text for text in metas.get("rejected_waste") or [] if text]
            if not accepted and not rejected:
                continue
            types = metas.get("garbage_types") or []
            if len(types) != 1 or types[0] in guide:
                continue
            code = types[0]
            guide[code] = {
                "type": code,
                "label": garbage_label(code, self.language),
                "color": garbage_color(code),
                "mode": metas.get("collection_mode"),
                "accepted": accepted,
                "rejected": rejected,
                "rules": _plain_text(metas.get("collection_rules_blurb")),
                "note": _plain_text(metas.get("waste_blurb")),
            }
        return list(guide.values())

    @staticmethod
    def _build_contacts(collections: list[dict[str, Any]]) -> dict[str, str]:
        """Coordonnées du service déchets de la MEL."""
        kinds = {
            "Email": "email",
            "TollFreePhoneNumber": "phone",
            "PhoneNumber": "phone",
            "Form": "form",
        }
        contacts: dict[str, str] = {}
        for collection in collections:
            for contact in collection.get("contacts") or []:
                kind = kinds.get(contact.get("type"))
                value = (contact.get("metas") or {}).get("value")
                if kind and value and kind not in contacts:
                    contacts[kind] = value
        return contacts
