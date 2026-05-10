"""Tests pour le client API Publidata."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from custom_components.mel_collecte.api import MelCollecteAPI, MAX_GEOCODE_CACHE_SIZE


class DummyResponse:
    """Réponse factice pour aiohttp."""

    def __init__(self, json_data, status=200):
        self._json = json_data
        self.status = status

    async def json(self):
        return self._json

    def raise_for_status(self):
        if self.status >= 400:
            raise Exception(f"HTTP {self.status}")


class TestGeocodeAddress:
    """Tests de geocode_address()."""

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached(self):
        """Un cache hit retourne la valeur cached."""
        session = MagicMock()
        api = MelCollecteAPI(session)

        cached_feature = {
            "geometry": {"coordinates": [2.0, 50.0]},
            "properties": {"id": "CACHED"},
        }
        api._geocode_cache["test address|"] = cached_feature

        result = await api.geocode_address("Test Address")
        assert result == cached_feature

    @pytest.mark.asyncio
    async def test_cache_key_includes_citycode(self):
        """La cache key inclut le citycode."""
        session = MagicMock()
        api = MelCollecteAPI(session)

        cached_no_cc = {
            "geometry": {"coordinates": [2.0, 50.0]},
            "properties": {"id": "NO_CC"},
        }
        cached_with_cc = {
            "geometry": {"coordinates": [3.0, 51.0]},
            "properties": {"id": "WITH_CC"},
        }

        api._geocode_cache["test|"] = cached_no_cc
        api._geocode_cache["test|59350"] = cached_with_cc

        result1 = await api.geocode_address("Test", None)
        result2 = await api.geocode_address("Test", "59350")

        assert result1 == cached_no_cc
        assert result2 == cached_with_cc

    @pytest.mark.asyncio
    async def test_empty_response_returns_none(self):
        """Une réponse vide retourne None."""
        session = MagicMock()
        session.get = AsyncMock(return_value=DummyResponse([]))
        api = MelCollecteAPI(session)

        result = await api.geocode_address("Test Address")
        assert result is None

    @pytest.mark.asyncio
    async def test_response_without_data_returns_none(self):
        """Une réponse sans 'data' retourne None."""
        session = MagicMock()
        session.get = AsyncMock(return_value=DummyResponse([{"other": "field"}]))
        api = MelCollecteAPI(session)

        result = await api.geocode_address("Test Address")
        assert result is None

    @pytest.mark.asyncio
    async def test_response_without_features_returns_none(self):
        """Une réponse sans 'features' retourne None."""
        session = MagicMock()
        session.get = AsyncMock(
            return_value=DummyResponse([{"data": {"other": "field"}}])
        )
        api = MelCollecteAPI(session)

        result = await api.geocode_address("Test Address")
        assert result is None

    @pytest.mark.asyncio
    async def test_valid_response_caches_and_returns(self):
        """Une réponse valide est cachée et retournée."""
        session = MagicMock()
        expected_feature = {
            "geometry": {"coordinates": [3.0, 50.6]},
            "properties": {"id": "TEST_ID"},
        }
        session.get = AsyncMock(
            return_value=DummyResponse([{"data": {"features": [expected_feature]}}])
        )
        api = MelCollecteAPI(session)

        result = await api.geocode_address("5 rue du Test")

        assert result == expected_feature
        cache_key = "5 rue du test|"
        assert cache_key in api._geocode_cache

    @pytest.mark.asyncio
    async def test_cache_eviction_at_limit(self):
        """Quand le cache atteint 100 entrées, il est vidé."""
        session = MagicMock()
        api = MelCollecteAPI(session)

        for i in range(MAX_GEOCODE_CACHE_SIZE):
            api._geocode_cache[f"address_{i}|"] = {"geometry": {"coordinates": [0, 0]}}

        assert len(api._geocode_cache) == MAX_GEOCODE_CACHE_SIZE

        new_feature = {
            "geometry": {"coordinates": [1.0, 1.0]},
            "properties": {"id": "NEW"},
        }
        session.get = AsyncMock(
            return_value=DummyResponse([{"data": {"features": [new_feature]}}])
        )

        await api.geocode_address("New Address")
        assert len(api._geocode_cache) == 1


class TestFetchWasteCollections:
    """Tests de fetch_waste_collections()."""

    @pytest.mark.asyncio
    async def test_missing_hits_returns_empty_list(self):
        """Si 'hits' est manquant, retourne une liste vide."""
        session = MagicMock()
        session.get = AsyncMock(return_value=DummyResponse({}))
        api = MelCollecteAPI(session)

        result = await api.fetch_waste_collections("876", "ADDR_ID")
        assert result == []

    @pytest.mark.asyncio
    async def test_missing_hits_list_returns_empty_list(self):
        """Si 'hits.hits' est manquant, retourne une liste vide."""
        session = MagicMock()
        session.get = AsyncMock(return_value=DummyResponse({"hits": {}}))
        api = MelCollecteAPI(session)

        result = await api.fetch_waste_collections("876", "ADDR_ID")
        assert result == []

    @pytest.mark.asyncio
    async def test_valid_response_returns_sources(self):
        """Une réponse valide retourne les _source des hits."""
        session = MagicMock()
        expected_source = {"id": "COL_1", "name": "Collecte OMR"}
        session.get = AsyncMock(
            return_value=DummyResponse(
                {
                    "hits": {
                        "hits": [
                            {"_source": expected_source},
                            {"_source": {"id": "COL_2"}},
                        ]
                    }
                }
            )
        )
        api = MelCollecteAPI(session)

        result = await api.fetch_waste_collections("876", "ADDR_ID")

        assert len(result) == 2
        assert result[0]["id"] == "COL_1"
        assert result[1]["id"] == "COL_2"

    @pytest.mark.asyncio
    async def test_hit_without_source_skipped(self):
        """Un hit sans _source est ignoré."""
        session = MagicMock()
        session.get = AsyncMock(
            return_value=DummyResponse(
                {
                    "hits": {
                        "hits": [
                            {"_source": {"id": "COL_1"}},
                            {},  # sans _source
                            {"_source": {"id": "COL_2"}},
                        ]
                    }
                }
            )
        )
        api = MelCollecteAPI(session)

        result = await api.fetch_waste_collections("876", "ADDR_ID")
        assert len(result) == 2

    @pytest.mark.asyncio
    async def test_lat_lon_parameters_passed(self):
        """Les paramètres lat/lon sont inclus dans la requête."""
        session = MagicMock()
        mock_get = AsyncMock(return_value=DummyResponse({"hits": {"hits": []}}))
        session.get = mock_get
        api = MelCollecteAPI(session)

        await api.fetch_waste_collections("876", "ADDR_ID", lat=50.6, lon=3.0)

        call_args = mock_get.call_args
        params = call_args[1]["params"]
        assert ("lat", "50.6") in params
        assert ("lon", "3.0") in params


class TestFetchAlerts:
    """Tests de fetch_alerts()."""

    @pytest.mark.asyncio
    async def test_missing_hits_returns_empty_list(self):
        """Si 'hits' est manquant, retourne une liste vide."""
        session = MagicMock()
        session.get = AsyncMock(return_value=DummyResponse({}))
        api = MelCollecteAPI(session)

        result = await api.fetch_alerts("876", "ADDR_ID")
        assert result == []

    @pytest.mark.asyncio
    async def test_default_size_is_5(self):
        """Par défaut, size=5."""
        session = MagicMock()
        mock_get = AsyncMock(return_value=DummyResponse({"hits": {"hits": []}}))
        session.get = mock_get
        api = MelCollecteAPI(session)

        await api.fetch_alerts("876", "ADDR_ID")

        call_args = mock_get.call_args
        params = call_args[1]["params"]
        size_param = dict(params).get("size")
        assert size_param == "5"

    @pytest.mark.asyncio
    async def test_custom_size(self):
        """Un size personnalisé est respecté."""
        session = MagicMock()
        mock_get = AsyncMock(return_value=DummyResponse({"hits": {"hits": []}}))
        session.get = mock_get
        api = MelCollecteAPI(session)

        await api.fetch_alerts("876", "ADDR_ID", size=10)

        call_args = mock_get.call_args
        params = call_args[1]["params"]
        size_param = dict(params).get("size")
        assert size_param == "10"
