"""Client HTTP pour l'API Publidata."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import aiohttp
import async_timeout
from aiohttp import ClientSession

from .const import (
    GEO_URL,
    MAX_RETRIES,
    RETRY_BASE_DELAY,
    RETRY_MAX_DELAY,
    SEARCH_URL,
    PermanentError,
    TransientError,
)

LOGGER = logging.getLogger(__name__)


MAX_GEOCODE_CACHE_SIZE = 100

# HTTP status codes that should never trigger a retry
_NON_RETRIABLE_STATUS = {400, 401, 403, 404, 422}


def _classify_http_error(status: int) -> None:
    """Lève TransientError ou PermanentError selon le code HTTP.

    Les erreurs 5xx et 429 sont transitoires (réseau, serveur surchargé).
    Les erreurs 4xx (sauf 429) sont permanentes.
    """
    if status in _NON_RETRIABLE_STATUS:
        raise PermanentError(f"HTTP {status} — erreur permanente, pas de nouvel essai")
    if status == 429 or status >= 500:
        raise TransientError(f"HTTP {status} — erreur transitoire, réessai en cours")
    # autres 4xx non listés → permanentes par défaut
    if status >= 400:
        raise PermanentError(f"HTTP {status} — erreur permanente, pas de nouvel essai")


class MelCollecteAPI:
    """Fournit les appels nécessaires à l'intégration."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session
        self._geocode_cache: dict[str, dict[str, Any]] = {}
        self._last_error: str | None = None

    @property
    def last_error(self) -> str | None:
        """Retourne le dernier message d'erreur enregistré."""
        return self._last_error

    async def _request_with_retry(
        self,
        url: str,
        params: Any,
    ) -> Any:
        """Effectue une requête GET avec réessais et backoff exponentiel.

        Réessaie en cas d'erreur transitoire jusqu'à MAX_RETRIES fois.
        Respecte l'en-tête Retry-After en cas de HTTP 429.
        Lève UpdateFailed (via TransientError/PermanentError) après épuisement.
        """
        last_exc: Exception | None = None

        for attempt in range(MAX_RETRIES + 1):
            try:
                async with async_timeout.timeout(20):
                    response = await self._session.get(url, params=params)

                # Gestion HTTP 429 avec Retry-After
                if response.status == 429:
                    retry_after_raw = response.headers.get("Retry-After")
                    try:
                        delay = (
                            min(float(retry_after_raw), RETRY_MAX_DELAY)
                            if retry_after_raw
                            else None
                        )
                    except (ValueError, TypeError):
                        delay = None

                    if delay is None:
                        delay = min(
                            RETRY_BASE_DELAY * (2**attempt),
                            RETRY_MAX_DELAY,
                        )

                    if attempt < MAX_RETRIES:
                        LOGGER.warning(
                            "HTTP 429 reçu (tentative %d/%d), attente %.1fs avant réessai",
                            attempt + 1,
                            MAX_RETRIES,
                            delay,
                        )
                        await asyncio.sleep(delay)
                        continue

                    raise TransientError(
                        f"HTTP 429 — limite de débit atteinte après {MAX_RETRIES} tentatives"
                    )

                # Gestion des autres erreurs HTTP
                if response.status >= 400:
                    _classify_http_error(response.status)

                return await response.json()

            except PermanentError:
                # Ne pas réessayer : remonter immédiatement
                raise
            except TransientError as exc:
                last_exc = exc
                if attempt < MAX_RETRIES:
                    delay = min(RETRY_BASE_DELAY * (2**attempt), RETRY_MAX_DELAY)
                    LOGGER.warning(
                        "Erreur transitoire (tentative %d/%d): %s — réessai dans %.1fs",
                        attempt + 1,
                        MAX_RETRIES,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    LOGGER.error(
                        "Erreur transitoire persistante après %d tentatives: %s",
                        MAX_RETRIES,
                        exc,
                    )
                    raise
            except (
                aiohttp.ClientConnectorError,
                aiohttp.ServerDisconnectedError,
                asyncio.TimeoutError,
            ) as exc:
                last_exc = exc
                if attempt < MAX_RETRIES:
                    delay = min(RETRY_BASE_DELAY * (2**attempt), RETRY_MAX_DELAY)
                    LOGGER.warning(
                        "Erreur réseau (tentative %d/%d): %s — réessai dans %.1fs",
                        attempt + 1,
                        MAX_RETRIES,
                        exc,
                        delay,
                    )
                    await asyncio.sleep(delay)
                else:
                    LOGGER.error(
                        "Erreur réseau persistante après %d tentatives: %s",
                        MAX_RETRIES,
                        exc,
                    )
                    raise TransientError(
                        f"Erreur réseau après {MAX_RETRIES} tentatives : {exc}"
                    ) from exc

        # Ce point ne devrait pas être atteint, mais par sécurité
        raise TransientError(
            f"Requête échouée après {MAX_RETRIES} tentatives : {last_exc}"
        )

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

        try:
            payload = await self._request_with_retry(GEO_URL, params)
            self._last_error = None
        except (TransientError, PermanentError) as exc:
            self._last_error = str(exc)
            raise

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

        try:
            payload = await self._request_with_retry(SEARCH_URL, params)
            self._last_error = None
        except (TransientError, PermanentError) as exc:
            self._last_error = str(exc)
            raise

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

        try:
            payload = await self._request_with_retry(SEARCH_URL, params)
            self._last_error = None
        except (TransientError, PermanentError) as exc:
            self._last_error = str(exc)
            raise

        hits = payload.get("hits", {})
        hits_list = hits.get("hits")
        if not hits_list or not isinstance(hits_list, list):
            return []
        return [hit.get("_source") for hit in hits_list if hit.get("_source")]
