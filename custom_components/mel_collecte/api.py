"""Client HTTP pour l'API Publidata."""

from __future__ import annotations

import logging
from typing import Any

import async_timeout
from aiohttp import ClientSession

from .const import GEO_URL, SEARCH_URL

LOGGER = logging.getLogger(__name__)


MAX_GEOCODE_CACHE_SIZE = 100


class MelCollecteAPI:
    """Fournit les appels nécessaires à l'intégration."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session
        self._geocode_cache: dict[str, dict[str, Any]] = {}

    async def geocode_address(
        self, address: str, citycode: str | None = None
    ) -> dict[str, Any] | None:
        """Retourne les détails géolocalisés d'une adresse."""
        cache_key = f"{address.lower()}|{citycode or ''}"
        if cache_key in self._geocode_cache:
            return self._geocode_cache[cache_key]

        params: dict[str, Any] = {
            "q": address,
            "limit": 1,
            "lookup": "publidata",
        }
        if citycode:
            params["citycode"] = citycode

        async with async_timeout.timeout(20):
            response = await self._session.get(GEO_URL, params=params)
            response.raise_for_status()
            payload = await response.json()

        if not payload or not isinstance(payload, list) or not payload[0]:
            return None
        data = payload[0].get("data")
        if not data:
            return None
        features = data.get("features")
        if not features or not isinstance(features, list):
            return None
        feature = features[0]
        if len(self._geocode_cache) >= MAX_GEOCODE_CACHE_SIZE:
            self._geocode_cache.clear()
        self._geocode_cache[cache_key] = feature
        return feature

    async def fetch_waste_collections(
        self,
        instance_id: str,
        address_id: str,
        lat: float | None = None,
        lon: float | None = None,
    ) -> list[dict[str, Any]]:
        """Récupère les collectes associées à l'adresse."""
        params: list[tuple[str, str]] = [
            ("types[]", "Platform::Services::WasteCollection"),
            ("instances[]", instance_id),
            ("address_id", address_id),
            ("size", "999"),
        ]
        if lat is not None and lon is not None:
            params.extend(
                [
                    ("lat", str(lat)),
                    ("lon", str(lon)),
                ]
            )

        async with async_timeout.timeout(20):
            response = await self._session.get(SEARCH_URL, params=params)
            response.raise_for_status()
            payload = await response.json()

        hits = payload.get("hits", {})
        hits_list = hits.get("hits")
        if not hits_list or not isinstance(hits_list, list):
            return []
        return [hit.get("_source") for hit in hits_list if hit.get("_source")]

    async def fetch_alerts(
        self,
        instance_id: str,
        address_id: str,
        size: int = 5,
    ) -> list[dict[str, Any]]:
        """Récupère les alertes du service de collecte."""
        params: list[tuple[str, str]] = [
            ("types[]", "Alert"),
            ("states[]", "visible"),
            ("include[]", "*model_name"),
            ("instances[]", instance_id),
            ("order[desc]", "published_at"),
            ("address_id", address_id),
            ("size", str(size)),
        ]

        async with async_timeout.timeout(20):
            response = await self._session.get(SEARCH_URL, params=params)
            response.raise_for_status()
            payload = await response.json()

        hits = payload.get("hits", {})
        hits_list = hits.get("hits")
        if not hits_list or not isinstance(hits_list, list):
            return []
        return [hit.get("_source") for hit in hits_list if hit.get("_source")]
