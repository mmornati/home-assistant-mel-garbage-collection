"""Client HTTP pour l'API Publidata."""

from __future__ import annotations

import logging
from typing import Any

import async_timeout
from aiohttp import ClientSession

from .const import GEO_URL, SEARCH_URL

LOGGER = logging.getLogger(__name__)


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

        features = payload[0]["data"]["features"] if payload else []
        if not features:
            return None
        feature = features[0]
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

        return [hit["_source"] for hit in payload["hits"]["hits"]]
