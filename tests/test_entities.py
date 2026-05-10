"""Tests des entités de l'intégration (calendrier et capteurs)."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from custom_components.mel_collecte.calendar import MelCollecteCalendar
from custom_components.mel_collecte.sensor import (
    MelCollecteNextSensor,
    MelCollecteTypeSensor,
)


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

    with patch(
        "custom_components.mel_collecte.calendar.dt_util.utcnow",
        return_value=reference_now,
    ):
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

    with patch(
        "custom_components.mel_collecte.sensor.dt_util.utcnow",
        return_value=reference_now,
    ):
        value = sensor.native_value
        attrs = sensor.extra_state_attributes

    assert value is not None
    assert attrs["types_friendly"] == ["Ordures ménagères résiduelles"]


def test_type_sensor_name_and_value():
    coordinator = DummyCoordinator(_sample_events(), _sample_collections())
    entry = SimpleNamespace(entry_id="test")
    sensor = MelCollecteTypeSensor(coordinator, entry, "dv")
    reference_now = datetime(2025, 1, 1, tzinfo=timezone.utc)

    with patch(
        "custom_components.mel_collecte.sensor.dt_util.utcnow",
        return_value=reference_now,
    ):
        value = sensor.native_value

    assert sensor.name == "Collecte Déchets verts"
    assert value == "2025-01-09T00:00:00+00:00"


def test_alert_sensor_count_and_attributes():
    """Test du capteur d'alertes."""
    from custom_components.mel_collecte.sensor import MelCollecteAlertSensor

    sample_alerts = [
        {
            "id": 5534,
            "name": "Conditions météorologiques",
            "alert_type": "danger",
            "alert_type_friendly": "⚠️ Alerte",
            "blurb": "<p>Suite aux derniers mouvements sociaux...</p>",
            "start_at": "2026-01-06T08:11:00.000Z",
            "end_at": "2026-01-10T17:00:00.000Z",
            "published_at": "2026-01-06T08:11:00.000Z",
        },
        {
            "id": 5411,
            "name": "Encombrants sur Rendez-Vous",
            "alert_type": "info",
            "alert_type_friendly": "ℹ️ Information",
            "blurb": "<p>À partir du 1er janvier 2026...</p>",
            "start_at": "2026-01-01T07:00:00.000Z",
            "end_at": "2026-02-01T07:00:00.000Z",
            "published_at": "2026-01-01T07:00:00.000Z",
        },
    ]

    class AlertCoordinator:
        def __init__(self, alerts):
            self.data = {"events": [], "collections": [], "alerts": alerts}

        async def async_request_refresh(self):
            return None

    coordinator = AlertCoordinator(sample_alerts)
    entry = SimpleNamespace(entry_id="test")
    sensor = MelCollecteAlertSensor(coordinator, entry)

    # Test native value (count)
    assert sensor.native_value == 2

    # Test attributes
    attrs = sensor.extra_state_attributes
    assert "alerts" in attrs
    assert len(attrs["alerts"]) == 2
    assert attrs["last_alert_name"] == "Conditions météorologiques"
    assert attrs["last_alert_type"] == "danger"


def test_alert_sensor_empty():
    """Test du capteur d'alertes sans alertes."""
    from custom_components.mel_collecte.sensor import MelCollecteAlertSensor

    class AlertCoordinator:
        def __init__(self):
            self.data = {"events": [], "collections": [], "alerts": []}

        async def async_request_refresh(self):
            return None

    coordinator = AlertCoordinator()
    entry = SimpleNamespace(entry_id="test")
    sensor = MelCollecteAlertSensor(coordinator, entry)

    assert sensor.native_value == 0
    attrs = sensor.extra_state_attributes
    assert attrs["alerts"] == []
