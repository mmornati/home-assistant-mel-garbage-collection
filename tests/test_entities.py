"""Tests des entités de l'intégration (calendrier et capteurs)."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from custom_components.mel_collecte.calendar import MelCollecteCalendar
from custom_components.mel_collecte.sensor import MelCollecteNextSensor, MelCollecteTypeSensor


class DummyCoordinator:
    """Objet simple imitant le coordinator."""

    def __init__(self, events, collections):
        self.data = {"events": events, "collections": collections}

    async def async_request_refresh(self):
        return None


def _sample_events():
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    first_start = now + timedelta(days=1)
    second_start = now + timedelta(days=8)
    return [
        {
            "collection_id": "col_omr",
            "garbage_types": ["omr"],
            "garbage_types_friendly": ["Ordures ménagères résiduelles"],
            "collection_mode": "door",
            "start": first_start,
            "end": first_start + timedelta(hours=2),
            "name": "Collecte OMR",
        },
        {
            "collection_id": "col_dv",
            "garbage_types": ["dv"],
            "garbage_types_friendly": ["Déchets verts"],
            "collection_mode": "door",
            "start": second_start,
            "end": second_start + timedelta(hours=2),
            "name": "Collecte DV",
        },
    ]


def _sample_collections():
    return [
        {
            "id": "col_omr",
            "name": "Collecte OMR",
            "garbage_types": ["omr"],
            "garbage_types_friendly": ["Ordures ménagères résiduelles"],
            "collection_mode": "door",
            "accepted_waste": [],
            "rejected_waste": [],
            "occurrences": [],
        },
        {
            "id": "col_dv",
            "name": "Collecte DV",
            "garbage_types": ["dv"],
            "garbage_types_friendly": ["Déchets verts"],
            "collection_mode": "door",
            "accepted_waste": [],
            "rejected_waste": [],
            "occurrences": [],
        },
    ]


def test_calendar_event_summary():
    coordinator = DummyCoordinator(_sample_events(), _sample_collections())
    entry = SimpleNamespace(entry_id="test")
    calendar = MelCollecteCalendar(coordinator, entry)
    reference_now = datetime(2025, 1, 1, tzinfo=timezone.utc)

    with patch("custom_components.mel_collecte.calendar.dt_util.utcnow", return_value=reference_now):
        event = calendar.event

    assert event is not None
    assert event.summary == "Ordures ménagères résiduelles"
    assert "Collecte OMR" in event.description


@pytest.mark.asyncio
async def test_calendar_async_get_events():
    coordinator = DummyCoordinator(_sample_events(), _sample_collections())
    entry = SimpleNamespace(entry_id="test")
    calendar = MelCollecteCalendar(coordinator, entry)
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2025, 1, 31, tzinfo=timezone.utc)

    events = await calendar.async_get_events(None, start, end)
    assert len(events) == 2
    assert {evt.summary for evt in events} == {
        "Ordures ménagères résiduelles",
        "Déchets verts",
    }


def test_next_sensor_attributes():
    coordinator = DummyCoordinator(_sample_events(), _sample_collections())
    entry = SimpleNamespace(entry_id="test")
    sensor = MelCollecteNextSensor(coordinator, entry)
    reference_now = datetime(2025, 1, 1, tzinfo=timezone.utc)

    with patch("custom_components.mel_collecte.sensor.dt_util.utcnow", return_value=reference_now):
        value = sensor.native_value
        attrs = sensor.extra_state_attributes

    assert value is not None
    assert attrs["types_friendly"] == ["Ordures ménagères résiduelles"]


def test_type_sensor_name_and_value():
    coordinator = DummyCoordinator(_sample_events(), _sample_collections())
    entry = SimpleNamespace(entry_id="test")
    sensor = MelCollecteTypeSensor(coordinator, entry, "dv")
    reference_now = datetime(2025, 1, 1, tzinfo=timezone.utc)

    with patch("custom_components.mel_collecte.sensor.dt_util.utcnow", return_value=reference_now):
        value = sensor.native_value

    assert sensor.name == "Collecte Déchets verts"
    assert value.endswith("T08:00:00+00:00")
