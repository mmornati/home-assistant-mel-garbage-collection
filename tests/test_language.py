"""Tests de l'option de langue (français par défaut, anglais en option)."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from custom_components.mel_collecte.calendar import MelCollecteCalendar
from custom_components.mel_collecte.config_flow import (
    MelCollecteConfigFlow,
    MelCollecteOptionsFlow,
)
from custom_components.mel_collecte.const import (
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    get_entry_language,
    ui_text,
)
from custom_components.mel_collecte.sensor import (
    MelCollecteAlertSensor,
    MelCollecteNextCollectionDaysSensor,
    MelCollecteNextSensor,
    MelCollecteTypeDaysSensor,
    MelCollecteTypeSensor,
)


class DummyCoordinator:
    def __init__(self, events):
        self.data = {"events": events, "collections": [], "alerts": []}


def _events():
    start = datetime(2025, 1, 2, tzinfo=timezone.utc)
    return [
        {
            "collection_id": "col_dv",
            "garbage_types": ["dv"],
            "garbage_types_friendly": ["Déchets verts"],
            "collection_mode": "door",
            "start": start,
            "end": start + timedelta(hours=2),
            "name": "Collecte DV",
        }
    ]


def _entry(language=None, in_options=True):
    store = {CONF_LANGUAGE: language} if language else {}
    if in_options:
        return SimpleNamespace(entry_id="test", options=store, data={})
    return SimpleNamespace(entry_id="test", options={}, data=store)


class TestGetEntryLanguage:
    def test_default_is_french(self):
        assert DEFAULT_LANGUAGE == "fr"
        assert get_entry_language(SimpleNamespace(entry_id="x")) == "fr"
        assert get_entry_language(_entry()) == "fr"

    def test_reads_data_then_options(self):
        assert get_entry_language(_entry("en", in_options=False)) == "en"
        entry = SimpleNamespace(
            entry_id="x", data={CONF_LANGUAGE: "en"}, options={CONF_LANGUAGE: "fr"}
        )
        assert get_entry_language(entry) == "fr"

    def test_unsupported_language_falls_back_to_french(self):
        assert get_entry_language(_entry("de")) == "fr"

    def test_ui_text_formats_labels(self):
        assert ui_text("type_collection", "fr", label="Verre") == "Collecte Verre"
        assert ui_text("type_collection", "en", label="Glass") == "Glass collection"
        assert ui_text("days_unit", "xx") == "jours"


class TestSensorNames:
    @pytest.mark.parametrize(
        "language,expected",
        [
            (
                "fr",
                {
                    "next": "Prochaine collecte",
                    "days": "Jours avant prochaine collecte",
                    "alerts": "Alertes collecte",
                    "type": "Collecte Déchets verts",
                    "type_days": "Collecte Déchets verts dans",
                    "unit": "jours",
                    "device": "Collectes MEL",
                },
            ),
            (
                "en",
                {
                    "next": "Next collection",
                    "days": "Days until next collection",
                    "alerts": "Collection alerts",
                    "type": "Green waste collection",
                    "type_days": "Green waste collection in",
                    "unit": "days",
                    "device": "MEL Collections",
                },
            ),
        ],
    )
    def test_names_follow_language(self, language, expected):
        coordinator = DummyCoordinator(_events())
        entry = _entry(language)

        assert MelCollecteNextSensor(coordinator, entry).name == expected["next"]
        days = MelCollecteNextCollectionDaysSensor(coordinator, entry)
        assert days.name == expected["days"]
        assert days._attr_native_unit_of_measurement == expected["unit"]
        assert MelCollecteAlertSensor(coordinator, entry).name == expected["alerts"]
        assert MelCollecteTypeSensor(coordinator, entry, "dv").name == expected["type"]
        type_days = MelCollecteTypeDaysSensor(coordinator, entry, "dv")
        assert type_days.name == expected["type_days"]
        assert type_days._attr_native_unit_of_measurement == expected["unit"]
        assert type_days.device_info.name == expected["device"]


class TestCalendarLanguage:
    def test_calendar_defaults_to_french_even_if_hass_is_english(self):
        coordinator = DummyCoordinator(_events())
        calendar = MelCollecteCalendar(coordinator, _entry())
        calendar.hass = SimpleNamespace(config=SimpleNamespace(language="en"))

        with patch(
            "custom_components.mel_collecte.calendar.dt_util.utcnow",
            return_value=datetime(2025, 1, 1, tzinfo=timezone.utc),
        ):
            event = calendar.event

        assert event.summary == "Déchets verts"
        assert calendar.device_info.name == "Collectes MEL"

    def test_calendar_in_english_when_configured(self):
        coordinator = DummyCoordinator(_events())
        calendar = MelCollecteCalendar(coordinator, _entry("en"))

        with patch(
            "custom_components.mel_collecte.calendar.dt_util.utcnow",
            return_value=datetime(2025, 1, 1, tzinfo=timezone.utc),
        ):
            event = calendar.event

        assert event.summary == "Green waste"
        assert calendar.device_info.name == "MEL Collections"


class TestConfigFlowLanguage:
    async def _create(self, user_input):
        mock_api = MagicMock()
        mock_api.geocode_address = AsyncMock(
            return_value={
                "geometry": {"coordinates": [3.0, 50.6]},
                "properties": {"id": "MEL_ID_123"},
            }
        )
        mock_api.fetch_waste_collections = AsyncMock(return_value=[{"id": "COL_1"}])
        with patch(
            "custom_components.mel_collecte.config_flow.async_get_clientsession",
            return_value=MagicMock(),
        ), patch(
            "custom_components.mel_collecte.config_flow.MelCollecteAPI",
            return_value=mock_api,
        ):
            flow = MelCollecteConfigFlow(MagicMock())
            return await flow.async_step_user(user_input)

    @pytest.mark.asyncio
    async def test_entry_defaults_to_french(self):
        result = await self._create({"address": "5 rue de Lille, Lille"})
        assert result["data"][CONF_LANGUAGE] == "fr"

    @pytest.mark.asyncio
    async def test_entry_stores_chosen_language(self):
        result = await self._create(
            {"address": "5 rue de Lille, Lille", CONF_LANGUAGE: "en"}
        )
        assert result["data"][CONF_LANGUAGE] == "en"

    @pytest.mark.asyncio
    async def test_options_form_has_language_with_current_value(self):
        flow = MelCollecteOptionsFlow.__new__(MelCollecteOptionsFlow)
        flow.config_entry = SimpleNamespace(
            options={}, data={CONF_LANGUAGE: "en"}, entry_id="x"
        )
        flow.async_show_form = lambda **kwargs: kwargs

        result = await flow.async_step_init()

        schema = result["data_schema"].schema
        language_key = next(k for k in schema if str(k) == CONF_LANGUAGE)
        assert language_key.default() == "en"

    @pytest.mark.asyncio
    async def test_options_save_language(self):
        flow = MelCollecteOptionsFlow.__new__(MelCollecteOptionsFlow)
        flow.config_entry = SimpleNamespace(options={}, data={}, entry_id="x")
        flow.async_create_entry = lambda **kwargs: kwargs

        result = await flow.async_step_init({"visible_types": "", CONF_LANGUAGE: "en"})

        assert result["data"][CONF_LANGUAGE] == "en"
