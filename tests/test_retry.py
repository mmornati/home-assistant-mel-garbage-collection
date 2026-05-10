"""Tests de la logique de réessai et de classification d'erreurs dans api.py."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.mel_collecte.api import MelCollecteAPI
from custom_components.mel_collecte.const import (
    MAX_RETRIES,
    RETRY_BASE_DELAY,
    PermanentError,
    TransientError,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeResponse:
    """Réponse HTTP factice configurable."""

    def __init__(self, json_data=None, status: int = 200, headers: dict | None = None):
        self._json = json_data or {}
        self.status = status
        self.headers = headers or {}

    async def json(self):
        return self._json

    def raise_for_status(self):
        if self.status >= 400:
            raise Exception(f"HTTP {self.status}")


# ---------------------------------------------------------------------------
# Tests de _classify_http_error
# ---------------------------------------------------------------------------


class TestClassifyHttpError:
    """Vérifie la classification des codes HTTP."""

    def _call(self, status: int):
        from custom_components.mel_collecte.api import _classify_http_error

        _classify_http_error(status)

    def test_400_is_permanent(self):
        with pytest.raises(PermanentError):
            self._call(400)

    def test_401_is_permanent(self):
        with pytest.raises(PermanentError):
            self._call(401)

    def test_403_is_permanent(self):
        with pytest.raises(PermanentError):
            self._call(403)

    def test_404_is_permanent(self):
        with pytest.raises(PermanentError):
            self._call(404)

    def test_422_is_permanent(self):
        with pytest.raises(PermanentError):
            self._call(422)

    def test_429_is_transient(self):
        with pytest.raises(TransientError):
            self._call(429)

    def test_500_is_transient(self):
        with pytest.raises(TransientError):
            self._call(500)

    def test_503_is_transient(self):
        with pytest.raises(TransientError):
            self._call(503)


# ---------------------------------------------------------------------------
# Tests de last_error
# ---------------------------------------------------------------------------


class TestLastError:
    """Vérifie que last_error est mis à jour correctement."""

    @pytest.mark.asyncio
    async def test_last_error_none_on_success(self):
        """last_error est None après une requête réussie."""
        session = MagicMock()
        session.get = AsyncMock(
            return_value=FakeResponse(
                [
                    {
                        "data": {
                            "features": [
                                {
                                    "geometry": {"coordinates": [3.0, 50.0]},
                                    "properties": {"id": "X"},
                                }
                            ]
                        }
                    }
                ]
            )
        )
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            await api.geocode_address("5 rue Test")

        assert api.last_error is None

    @pytest.mark.asyncio
    async def test_last_error_set_on_permanent_error(self):
        """last_error est renseigné après une erreur permanente."""
        session = MagicMock()
        session.get = AsyncMock(return_value=FakeResponse(status=404))
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock), pytest.raises(
            PermanentError
        ):
            await api.geocode_address("adresse inconnue")

        assert api.last_error is not None
        assert "404" in api.last_error

    @pytest.mark.asyncio
    async def test_last_error_set_on_transient_error_exhausted(self):
        """last_error est renseigné après épuisement des tentatives transitoires."""
        import aiohttp

        session = MagicMock()
        session.get = AsyncMock(side_effect=aiohttp.ClientConnectorError("timeout"))
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock), pytest.raises(
            TransientError
        ):
            await api.geocode_address("5 rue Test")

        assert api.last_error is not None


# ---------------------------------------------------------------------------
# Tests de réessai — erreurs réseau
# ---------------------------------------------------------------------------


class TestRetryOnNetworkErrors:
    """Vérifie les réessais sur erreurs réseau."""

    @pytest.mark.asyncio
    async def test_retries_on_client_connector_error(self):
        """ClientConnectorError déclenche MAX_RETRIES+1 tentatives au total."""
        import aiohttp

        session = MagicMock()
        session.get = AsyncMock(
            side_effect=aiohttp.ClientConnectorError("connection refused")
        )
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(TransientError):
                await api.geocode_address("5 rue Test")

        assert session.get.call_count == MAX_RETRIES + 1
        assert mock_sleep.call_count == MAX_RETRIES

    @pytest.mark.asyncio
    async def test_retries_on_server_disconnected(self):
        """ServerDisconnectedError déclenche les réessais."""
        import aiohttp

        session = MagicMock()
        session.get = AsyncMock(side_effect=aiohttp.ServerDisconnectedError())
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TransientError):
                await api.geocode_address("5 rue Test")

        assert session.get.call_count == MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_retries_on_timeout_error(self):
        """asyncio.TimeoutError déclenche les réessais."""
        session = MagicMock()
        session.get = AsyncMock(side_effect=asyncio.TimeoutError())
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TransientError):
                await api.geocode_address("5 rue Test")

        assert session.get.call_count == MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_succeeds_on_third_attempt(self):
        """Réussit après deux échecs réseau et un succès."""
        import aiohttp

        expected = [
            {
                "data": {
                    "features": [
                        {
                            "geometry": {"coordinates": [3.0, 50.0]},
                            "properties": {"id": "OK"},
                        }
                    ]
                }
            }
        ]
        session = MagicMock()
        session.get = AsyncMock(
            side_effect=[
                aiohttp.ClientConnectorError("err"),
                aiohttp.ClientConnectorError("err"),
                FakeResponse(expected),
            ]
        )
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await api.geocode_address("5 rue Test")

        assert result is not None
        assert result["properties"]["id"] == "OK"
        assert session.get.call_count == 3


# ---------------------------------------------------------------------------
# Tests de réessai — erreurs HTTP
# ---------------------------------------------------------------------------


class TestRetryOnHttpErrors:
    """Vérifie les réessais selon les codes HTTP."""

    @pytest.mark.asyncio
    async def test_no_retry_on_404(self):
        """HTTP 404 ne déclenche pas de réessai."""
        session = MagicMock()
        session.get = AsyncMock(return_value=FakeResponse(status=404))
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(PermanentError):
                await api.geocode_address("adresse inconnue")

        assert session.get.call_count == 1
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_retry_on_401(self):
        """HTTP 401 ne déclenche pas de réessai."""
        session = MagicMock()
        session.get = AsyncMock(return_value=FakeResponse(status=401))
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(PermanentError):
                await api.geocode_address("5 rue Test")

        assert session.get.call_count == 1
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_retry_on_500(self):
        """HTTP 500 déclenche les réessais."""
        session = MagicMock()
        session.get = AsyncMock(return_value=FakeResponse(status=500))
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TransientError):
                await api.geocode_address("5 rue Test")

        assert session.get.call_count == MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_retry_on_503(self):
        """HTTP 503 déclenche les réessais."""
        session = MagicMock()
        session.get = AsyncMock(return_value=FakeResponse(status=503))
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TransientError):
                await api.geocode_address("5 rue Test")

        assert session.get.call_count == MAX_RETRIES + 1


# ---------------------------------------------------------------------------
# Tests HTTP 429 avec Retry-After
# ---------------------------------------------------------------------------


class TestRateLimitHandling:
    """Vérifie la gestion du HTTP 429 et de l'en-tête Retry-After."""

    @pytest.mark.asyncio
    async def test_respects_retry_after_header(self):
        """Respect de l'en-tête Retry-After sur HTTP 429."""
        retry_after = "5"
        session = MagicMock()
        # Deux 429 puis succès
        good_response = FakeResponse(
            [
                {
                    "data": {
                        "features": [
                            {
                                "geometry": {"coordinates": [3.0, 50.0]},
                                "properties": {"id": "X"},
                            }
                        ]
                    }
                }
            ]
        )
        session.get = AsyncMock(
            side_effect=[
                FakeResponse(status=429, headers={"Retry-After": retry_after}),
                FakeResponse(status=429, headers={"Retry-After": retry_after}),
                good_response,
            ]
        )
        api = MelCollecteAPI(session)

        sleep_calls = []

        async def fake_sleep(delay):
            sleep_calls.append(delay)

        with patch("asyncio.sleep", side_effect=fake_sleep):
            result = await api.geocode_address("5 rue Test")

        assert result is not None
        # Les délais de sleep doivent correspondre à la valeur Retry-After
        assert sleep_calls[0] == pytest.approx(5.0)
        assert sleep_calls[1] == pytest.approx(5.0)

    @pytest.mark.asyncio
    async def test_uses_backoff_without_retry_after(self):
        """Utilise le backoff exponentiel si Retry-After est absent."""
        session = MagicMock()
        good_response = FakeResponse(
            [
                {
                    "data": {
                        "features": [
                            {
                                "geometry": {"coordinates": [3.0, 50.0]},
                                "properties": {"id": "X"},
                            }
                        ]
                    }
                }
            ]
        )
        session.get = AsyncMock(
            side_effect=[
                FakeResponse(status=429, headers={}),
                good_response,
            ]
        )
        api = MelCollecteAPI(session)

        sleep_calls = []

        async def fake_sleep(delay):
            sleep_calls.append(delay)

        with patch("asyncio.sleep", side_effect=fake_sleep):
            await api.geocode_address("5 rue Test")

        # Première tentative (attempt=0) → délai = RETRY_BASE_DELAY * 2^0 = 1s
        assert sleep_calls[0] == pytest.approx(RETRY_BASE_DELAY * (2**0))

    @pytest.mark.asyncio
    async def test_exhausted_429_raises_transient(self):
        """HTTP 429 persistant lève TransientError après MAX_RETRIES tentatives."""
        session = MagicMock()
        session.get = AsyncMock(return_value=FakeResponse(status=429, headers={}))
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TransientError):
                await api.geocode_address("5 rue Test")

        assert session.get.call_count == MAX_RETRIES + 1


# ---------------------------------------------------------------------------
# Tests du backoff exponentiel
# ---------------------------------------------------------------------------


class TestExponentialBackoff:
    """Vérifie la progression du délai entre les tentatives."""

    @pytest.mark.asyncio
    async def test_backoff_progression(self):
        """Le délai double à chaque tentative (jusqu'au cap RETRY_MAX_DELAY)."""
        import aiohttp

        session = MagicMock()
        session.get = AsyncMock(side_effect=aiohttp.ClientConnectorError("err"))
        api = MelCollecteAPI(session)

        sleep_calls = []

        async def fake_sleep(delay):
            sleep_calls.append(delay)

        with patch("asyncio.sleep", side_effect=fake_sleep):
            with pytest.raises(TransientError):
                await api.geocode_address("5 rue Test")

        assert len(sleep_calls) == MAX_RETRIES
        for i, delay in enumerate(sleep_calls):
            expected = min(RETRY_BASE_DELAY * (2**i), 30)
            assert delay == pytest.approx(expected)


# ---------------------------------------------------------------------------
# Tests d'intégration fetch_waste_collections et fetch_alerts
# ---------------------------------------------------------------------------


class TestFetchMethodsRetry:
    """Vérifie que fetch_waste_collections et fetch_alerts bénéficient aussi du retry."""

    @pytest.mark.asyncio
    async def test_fetch_waste_collections_retries_on_500(self):
        session = MagicMock()
        session.get = AsyncMock(return_value=FakeResponse(status=500))
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TransientError):
                await api.fetch_waste_collections("876", "ADDR_ID")

        assert session.get.call_count == MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_fetch_waste_collections_no_retry_on_404(self):
        session = MagicMock()
        session.get = AsyncMock(return_value=FakeResponse(status=404))
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            with pytest.raises(PermanentError):
                await api.fetch_waste_collections("876", "ADDR_ID")

        assert session.get.call_count == 1
        mock_sleep.assert_not_called()

    @pytest.mark.asyncio
    async def test_fetch_alerts_retries_on_503(self):
        session = MagicMock()
        session.get = AsyncMock(return_value=FakeResponse(status=503))
        api = MelCollecteAPI(session)

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(TransientError):
                await api.fetch_alerts("876", "ADDR_ID")

        assert session.get.call_count == MAX_RETRIES + 1

    @pytest.mark.asyncio
    async def test_normal_request_unaffected(self):
        """Une requête normale (200) fonctionne sans réessai."""
        session = MagicMock()
        session.get = AsyncMock(
            return_value=FakeResponse({"hits": {"hits": [{"_source": {"id": "C1"}}]}})
        )
        api = MelCollecteAPI(session)

        result = await api.fetch_waste_collections("876", "ADDR_ID")

        assert result == [{"id": "C1"}]
        assert session.get.call_count == 1
