"""Tests pour le config flow."""

from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from custom_components.mel_collecte.config_flow import (
    MelCollecteConfigFlow,
)


class DummyFlowResult:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


class TestMelCollecteConfigFlow:
    """Tests pour MelCollecteConfigFlow."""

    @pytest.fixture
    def mock_hass(self):
        hass = MagicMock()
        hass.loop = MagicMock()
        return hass

    @pytest.fixture
    def mock_session(self):
        return MagicMock()

    @pytest.mark.asyncio
    async def test_address_not_found_aborts(self, mock_hass, mock_session):
        """Une adresse non trouvée doit abort."""
        mock_api = MagicMock()
        mock_api.geocode_address = AsyncMock(return_value=None)

        with patch(
            "custom_components.mel_collecte.config_flow.async_get_clientsession",
            return_value=mock_session,
        ), patch(
            "custom_components.mel_collecte.config_flow.MelCollecteAPI",
            return_value=mock_api,
        ):
            flow = MelCollecteConfigFlow(mock_hass)
            result = await flow.async_step_user({"address": "Invalid Address"})

        assert result["type"] == "abort"
        assert result["reason"] == "address_not_found"

    @pytest.mark.asyncio
    async def test_address_without_id_aborts_outside_coverage(
        self, mock_hass, mock_session
    ):
        """Une adresse sans id doit abort avec outside_coverage."""
        mock_api = MagicMock()
        mock_api.geocode_address = AsyncMock(
            return_value={
                "geometry": {"coordinates": [2.3, 48.9]},
                "properties": {},
            }
        )

        with patch(
            "custom_components.mel_collecte.config_flow.async_get_clientsession",
            return_value=mock_session,
        ), patch(
            "custom_components.mel_collecte.config_flow.MelCollecteAPI",
            return_value=mock_api,
        ):
            flow = MelCollecteConfigFlow(mock_hass)
            result = await flow.async_step_user(
                {"address": "38 rue marcel sembat paris"}
            )

        assert result["type"] == "abort"
        assert result["reason"] == "outside_coverage"

    @pytest.mark.asyncio
    async def test_valid_mel_address_creates_entry(self, mock_hass, mock_session):
        """Une adresse MEL valide doit créer l'entrée."""
        mock_api = MagicMock()
        mock_api.geocode_address = AsyncMock(
            return_value={
                "geometry": {"coordinates": [3.0, 50.6]},
                "properties": {"id": "MEL_ID_123"},
            }
        )
        mock_api.fetch_waste_collections = AsyncMock(
            return_value=[{"id": "COL_1", "name": "OMR"}]
        )

        with patch(
            "custom_components.mel_collecte.config_flow.async_get_clientsession",
            return_value=mock_session,
        ), patch(
            "custom_components.mel_collecte.config_flow.MelCollecteAPI",
            return_value=mock_api,
        ):
            flow = MelCollecteConfigFlow(mock_hass)
            result = await flow.async_step_user({"address": "5 rue de Lille, Lille"})

        assert result["type"] == "create_entry"
        assert result["title"] == "5 rue de Lille, Lille"
        assert result["data"]["address"] == "5 rue de Lille, Lille"
        assert result["data"]["instance_id"] == "876"

    @pytest.mark.asyncio
    async def test_address_outside_mel_coverage_aborts(self, mock_hass, mock_session):
        """Une adresse hors zone MEL (sans collectes) doit abort."""
        mock_api = MagicMock()
        mock_api.geocode_address = AsyncMock(
            return_value={
                "geometry": {"coordinates": [2.3, 48.9]},
                "properties": {"id": "PARIS_ID_123"},
            }
        )
        mock_api.fetch_waste_collections = AsyncMock(return_value=[])

        with patch(
            "custom_components.mel_collecte.config_flow.async_get_clientsession",
            return_value=mock_session,
        ), patch(
            "custom_components.mel_collecte.config_flow.MelCollecteAPI",
            return_value=mock_api,
        ):
            flow = MelCollecteConfigFlow(mock_hass)
            result = await flow.async_step_user(
                {"address": "38 rue marcel sembat paris"}
            )

        assert result["type"] == "abort"
        assert result["reason"] == "outside_coverage"

    @pytest.mark.asyncio
    async def test_network_error_aborts_with_cannot_connect(self, mock_hass):
        """Une erreur réseau doit abort avec cannot_connect."""
        from aiohttp import ClientError

        mock_api = MagicMock()
        mock_api.geocode_address = AsyncMock(side_effect=ClientError())

        with patch(
            "custom_components.mel_collecte.config_flow.async_get_clientsession",
            return_value=MagicMock(),
        ), patch(
            "custom_components.mel_collecte.config_flow.MelCollecteAPI",
            return_value=mock_api,
        ):
            flow = MelCollecteConfigFlow(mock_hass)
            result = await flow.async_step_user({"address": "Lille"})

        assert result["type"] == "abort"
        assert result["reason"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_timeout_error_aborts_with_cannot_connect(self, mock_hass):
        """Un timeout doit abort avec cannot_connect."""
        import asyncio

        mock_api = MagicMock()
        mock_api.geocode_address = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch(
            "custom_components.mel_collecte.config_flow.async_get_clientsession",
            return_value=MagicMock(),
        ), patch(
            "custom_components.mel_collecte.config_flow.MelCollecteAPI",
            return_value=mock_api,
        ):
            flow = MelCollecteConfigFlow(mock_hass)
            result = await flow.async_step_user({"address": "Lille"})

        assert result["type"] == "abort"
        assert result["reason"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_timeout_on_fetch_collections_aborts(self, mock_hass):
        """Un timeout sur fetch_waste_collections doit abort."""
        import asyncio

        mock_api = MagicMock()
        mock_api.geocode_address = AsyncMock(
            return_value={
                "geometry": {"coordinates": [3.0, 50.6]},
                "properties": {"id": "MEL_ID"},
            }
        )
        mock_api.fetch_waste_collections = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch(
            "custom_components.mel_collecte.config_flow.async_get_clientsession",
            return_value=MagicMock(),
        ), patch(
            "custom_components.mel_collecte.config_flow.MelCollecteAPI",
            return_value=mock_api,
        ):
            flow = MelCollecteConfigFlow(mock_hass)
            result = await flow.async_step_user({"address": "Lille"})

        assert result["type"] == "abort"
        assert result["reason"] == "cannot_connect"

    @pytest.mark.asyncio
    async def test_client_error_on_fetch_collections_aborts(self, mock_hass):
        """Une ClientError sur fetch_waste_collections doit abort."""
        from aiohttp import ClientError

        mock_api = MagicMock()
        mock_api.geocode_address = AsyncMock(
            return_value={
                "geometry": {"coordinates": [3.0, 50.6]},
                "properties": {"id": "MEL_ID"},
            }
        )
        mock_api.fetch_waste_collections = AsyncMock(side_effect=ClientError())

        with patch(
            "custom_components.mel_collecte.config_flow.async_get_clientsession",
            return_value=MagicMock(),
        ), patch(
            "custom_components.mel_collecte.config_flow.MelCollecteAPI",
            return_value=mock_api,
        ):
            flow = MelCollecteConfigFlow(mock_hass)
            result = await flow.async_step_user({"address": "Lille"})

        assert result["type"] == "abort"
        assert result["reason"] == "cannot_connect"
