"""Tests des entités de l'intégration (calendrier et capteurs) - scénarios avancés."""

from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from custom_components.mel_collecte.calendar import MelCollecteCalendar
from custom_components.mel_collecte.sensor import (
    MelCollecteNextSensor,
    MelCollecteTypeSensor,
    MelCollecteTypeDaysSensor,
    MelCollecteAlertSensor,
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


class TestCalendarEdgeCases:
    """Tests des cas limites du calendrier."""

    def test_event_property_returns_none_when_all_in_past(self):
        """event retourne None si tous les événements sont passés."""
        now = datetime(2025, 1, 15, tzinfo=timezone.utc)
        past_events = [
            {
                "collection_id": "col_omr",
                "garbage_types": ["omr"],
                "garbage_types_friendly": ["Ordures ménagères résiduelles"],
                "collection_mode": "door",
                "start": now - timedelta(days=10),
                "end": now - timedelta(days=10) + timedelta(hours=2),
                "name": "Past Collection",
            },
        ]
        coordinator = DummyCoordinator(past_events, _sample_collections())
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry)

        with patch(
            "custom_components.mel_collecte.calendar.dt_util.utcnow", return_value=now
        ):
            event = calendar.event

        assert event is None

    def test_event_property_empty_events_returns_none(self):
        """event retourne None si la liste d'événements est vide."""
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        coordinator = DummyCoordinator([], [])
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry)

        with patch(
            "custom_components.mel_collecte.calendar.dt_util.utcnow", return_value=now
        ):
            event = calendar.event

        assert event is None

    def test_event_property_fallback_to_garbage_types(self):
        """event utilise garbage_types si garbage_types_friendly est absent."""
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = [
            {
                "collection_id": "col_omr",
                "garbage_types": ["omr"],
                "garbage_types_friendly": None,
                "collection_mode": "door",
                "start": now + timedelta(days=1),
                "end": now + timedelta(days=1, hours=2),
                "name": "Test Collection",
            },
        ]
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry)

        with patch(
            "custom_components.mel_collecte.calendar.dt_util.utcnow", return_value=now
        ):
            event = calendar.event

        assert event is not None
        assert "omr" in event.summary

    def test_event_property_fallback_to_name(self):
        """event utilise le nom si ni garbage_types_friendly ni garbage_types."""
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = [
            {
                "collection_id": "col_omr",
                "garbage_types": [],
                "garbage_types_friendly": [],
                "collection_mode": "door",
                "start": now + timedelta(days=1),
                "end": now + timedelta(days=1, hours=2),
                "name": "Named Collection",
            },
        ]
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry)

        with patch(
            "custom_components.mel_collecte.calendar.dt_util.utcnow", return_value=now
        ):
            event = calendar.event

        assert event is not None
        assert event.summary == "Named Collection"

    def test_extra_state_attributes(self):
        """extra_state_attributes retourne les infos de fetched_at et count."""
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = [
            {
                "collection_id": "col_omr",
                "garbage_types": ["omr"],
                "garbage_types_friendly": ["Ordures ménagères résiduelles"],
                "collection_mode": "door",
                "start": now + timedelta(days=1),
                "end": now + timedelta(days=1, hours=2),
                "name": "Test Collection",
            },
        ]
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry)

        attrs = calendar.extra_state_attributes
        assert "derniere_mise_a_jour" in attrs
        assert "nombre_evenements" in attrs
        assert attrs["nombre_evenements"] == 1


class TestCalendarTypeFiltering:
    """Tests du filtrage par type de déchet dans le calendrier (issue #15)."""

    def _make_events(self, now):
        return [
            {
                "collection_id": "col_omr",
                "garbage_types": ["omr"],
                "garbage_types_friendly": ["Ordures ménagères résiduelles"],
                "collection_mode": "door",
                "start": now + timedelta(days=1),
                "end": now + timedelta(days=1, hours=2),
                "name": "Collecte OMR",
            },
            {
                "collection_id": "col_dv",
                "garbage_types": ["dv"],
                "garbage_types_friendly": ["Déchets verts"],
                "collection_mode": "door",
                "start": now + timedelta(days=2),
                "end": now + timedelta(days=2, hours=2),
                "name": "Collecte DV",
            },
        ]

    def test_attr_has_time_is_true(self):
        """_attr_has_time doit être True pour améliorer le rendu dans la carte calendrier."""
        coordinator = DummyCoordinator([], [])
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry)
        assert calendar._attr_has_time is True

    def test_event_property_no_filter_returns_first_future(self):
        """Sans filtre, event retourne le premier événement futur (comportement inchangé)."""
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = self._make_events(now)
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry)

        with patch(
            "custom_components.mel_collecte.calendar.dt_util.utcnow", return_value=now
        ):
            event = calendar.event

        assert event is not None
        assert "Ordures ménagères résiduelles" in event.summary

    def test_event_property_filters_by_visible_types(self):
        """event retourne le premier événement futur correspondant aux types visibles."""
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = self._make_events(now)
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        # Only show "dv" — OMR should be skipped
        calendar = MelCollecteCalendar(coordinator, entry, visible_types=["dv"])

        with patch(
            "custom_components.mel_collecte.calendar.dt_util.utcnow", return_value=now
        ):
            event = calendar.event

        assert event is not None
        assert "Déchets verts" in event.summary

    def test_event_property_returns_none_when_no_type_matches(self):
        """event retourne None si aucun événement futur ne correspond au filtre."""
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = self._make_events(now)
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        # Filter for type that doesn't exist in events
        calendar = MelCollecteCalendar(coordinator, entry, visible_types=["enc"])

        with patch(
            "custom_components.mel_collecte.calendar.dt_util.utcnow", return_value=now
        ):
            event = calendar.event

        assert event is None

    def test_async_get_events_no_filter_returns_all_in_range(self):
        """Sans filtre, async_get_events retourne tous les événements dans la plage."""
        import asyncio

        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = self._make_events(now)
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry)

        start = now
        end = now + timedelta(days=30)
        result = asyncio.run(calendar.async_get_events(None, start, end))

        assert len(result) == 2

    def test_async_get_events_filters_by_visible_types(self):
        """async_get_events ne retourne que les événements correspondant aux types visibles."""
        import asyncio

        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = self._make_events(now)
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry, visible_types=["omr"])

        start = now
        end = now + timedelta(days=30)
        result = asyncio.run(calendar.async_get_events(None, start, end))

        assert len(result) == 1
        assert "Ordures ménagères résiduelles" in result[0].summary

    def test_async_get_events_excludes_all_when_no_type_matches(self):
        """async_get_events retourne une liste vide si le filtre ne correspond à rien."""
        import asyncio

        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = self._make_events(now)
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry, visible_types=["enc"])

        start = now
        end = now + timedelta(days=30)
        result = asyncio.run(calendar.async_get_events(None, start, end))

        assert result == []

    def test_visible_types_empty_list_shows_all(self):
        """visible_types=[] (liste vide) désactive le filtre — tous les événements sont retournés."""
        import asyncio

        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = self._make_events(now)
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        calendar = MelCollecteCalendar(coordinator, entry, visible_types=[])

        start = now
        end = now + timedelta(days=30)
        result = asyncio.run(calendar.async_get_events(None, start, end))

        assert len(result) == 2


class TestSensorEdgeCases:
    """Tests des cas limites des capteurs."""

    def test_next_sensor_no_events_returns_none_value(self):
        """MelCollecteNextSensor retourne None si pas d'événements."""
        now = datetime(2025, 1, 15, tzinfo=timezone.utc)
        past_events = [
            {
                "collection_id": "col_omr",
                "garbage_types": ["omr"],
                "garbage_types_friendly": ["Ordures ménagères résiduelles"],
                "collection_mode": "door",
                "start": now - timedelta(days=5),
                "end": now - timedelta(days=5) + timedelta(hours=2),
                "name": "Past Collection",
            },
        ]
        coordinator = DummyCoordinator(past_events, [])
        entry = SimpleNamespace(entry_id="test")
        sensor = MelCollecteNextSensor(coordinator, entry)

        with patch(
            "custom_components.mel_collecte.sensor.dt_util.utcnow", return_value=now
        ):
            value = sensor.native_value
            attrs = sensor.extra_state_attributes

        assert value is None
        assert attrs == {}

    def test_next_sensor_empty_events_returns_none_value(self):
        """MelCollecteNextSensor retourne None si pas d'événements du tout."""
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        coordinator = DummyCoordinator([], [])
        entry = SimpleNamespace(entry_id="test")
        sensor = MelCollecteNextSensor(coordinator, entry)

        with patch(
            "custom_components.mel_collecte.sensor.dt_util.utcnow", return_value=now
        ):
            value = sensor.native_value
            attrs = sensor.extra_state_attributes

        assert value is None
        assert attrs == {}

    def test_type_sensor_no_event_for_type_returns_none(self):
        """MelCollecteTypeSensor retourne None si pas d'événement pour ce type."""
        now = datetime(2025, 1, 1, tzinfo=timezone.utc)
        events = [
            {
                "collection_id": "col_omr",
                "garbage_types": ["omr"],
                "garbage_types_friendly": ["Ordures ménagères résiduelles"],
                "collection_mode": "door",
                "start": now + timedelta(days=1),
                "end": now + timedelta(days=1, hours=2),
                "name": "OMR Collection",
            },
        ]
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        sensor = MelCollecteTypeSensor(coordinator, entry, "dv")

        with patch(
            "custom_components.mel_collecte.sensor.dt_util.utcnow", return_value=now
        ):
            value = sensor.native_value
            attrs = sensor.extra_state_attributes

        assert value is None
        assert attrs == {}

    def test_type_sensor_past_events_returns_none(self):
        """MelCollecteTypeSensor retourne None si tous les événements sont passés."""
        now = datetime(2025, 1, 15, tzinfo=timezone.utc)
        events = [
            {
                "collection_id": "col_omr",
                "garbage_types": ["omr"],
                "garbage_types_friendly": ["Ordures ménagères résiduelles"],
                "collection_mode": "door",
                "start": now - timedelta(days=5),
                "end": now - timedelta(days=5) + timedelta(hours=2),
                "name": "Past OMR",
            },
        ]
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        sensor = MelCollecteTypeSensor(coordinator, entry, "omr")

        with patch(
            "custom_components.mel_collecte.sensor.dt_util.utcnow", return_value=now
        ):
            value = sensor.native_value

        assert value is None

    def test_type_sensor_name_uses_garbage_label(self):
        """MelCollecteTypeSensor utilise garbage_label pour le nom."""
        coordinator = DummyCoordinator([], [])
        entry = SimpleNamespace(entry_id="test")
        sensor = MelCollecteTypeSensor(coordinator, entry, "omr")

        assert "Ordures ménagères résiduelles" in sensor.name

    def test_type_days_sensor_calculates_days(self):
        """MelCollecteTypeDaysSensor calcule correctement le nombre de jours."""
        now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        events = [
            {
                "collection_id": "col_omr",
                "garbage_types": ["omr"],
                "garbage_types_friendly": ["Ordures ménagères résiduelles"],
                "collection_mode": "door",
                "start": now + timedelta(days=2),
                "end": now + timedelta(days=2, hours=2),
                "name": "OMR Collection",
            },
        ]
        coordinator = DummyCoordinator(events, [])
        entry = SimpleNamespace(entry_id="test")
        sensor = MelCollecteTypeDaysSensor(coordinator, entry, "omr")

        with patch(
            "custom_components.mel_collecte.sensor.dt_util.utcnow", return_value=now
        ), patch(
            "custom_components.mel_collecte.sensor.dt_util.now",
            return_value=now,
            create=True,
        ):
            value = sensor.native_value
            attrs = sensor.extra_state_attributes

        assert value == 2
        assert attrs["type"] == "omr"
        assert attrs["prochaine_collecte"] == events[0]["start"].isoformat()

    def test_type_days_sensor_returns_none_if_no_event(self):
        """MelCollecteTypeDaysSensor retourne None si aucun événement."""
        now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
        coordinator = DummyCoordinator([], [])
        entry = SimpleNamespace(entry_id="test")
        sensor = MelCollecteTypeDaysSensor(coordinator, entry, "omr")

        with patch(
            "custom_components.mel_collecte.sensor.dt_util.utcnow", return_value=now
        ), patch(
            "custom_components.mel_collecte.sensor.dt_util.now",
            return_value=now,
            create=True,
        ):
            value = sensor.native_value
            attrs = sensor.extra_state_attributes

        assert value is None
        assert attrs == {}

    def test_alert_sensor_with_alerts_native_value_is_count(self):
        """MelCollecteAlertSensor retourne le nombre d'alertes."""
        alerts = [
            {"id": 1, "name": "Alert 1", "alert_type": "danger"},
            {"id": 2, "name": "Alert 2", "alert_type": "warning"},
            {"id": 3, "name": "Alert 3", "alert_type": "info"},
        ]

        class AlertCoordinator:
            def __init__(self, alerts):
                self.data = {"events": [], "collections": [], "alerts": alerts}

            async def async_request_refresh(self):
                return None

        coordinator = AlertCoordinator(alerts)
        entry = SimpleNamespace(entry_id="test")
        sensor = MelCollecteAlertSensor(coordinator, entry)

        assert sensor.native_value == 3

    def test_alert_sensor_empty_attributes(self):
        """MelCollecteAlertSensor avec alertes vides retourne attributes vides."""

        class EmptyCoordinator:
            def __init__(self):
                self.data = {"events": [], "collections": [], "alerts": []}

            async def async_request_refresh(self):
                return None

        coordinator = EmptyCoordinator()
        entry = SimpleNamespace(entry_id="test")
        sensor = MelCollecteAlertSensor(coordinator, entry)

        attrs = sensor.extra_state_attributes
        assert attrs["alerts"] == []
        assert "last_alert_name" not in attrs
        assert "last_alert_type" not in attrs

    def test_device_info_returns_correct_identifiers(self):
        """Les capteurs ont les bons identifiers dans device_info."""
        coordinator = DummyCoordinator([], [])
        entry = SimpleNamespace(entry_id="test_entry_123")
        sensor = MelCollecteNextSensor(coordinator, entry)

        device_info = sensor.device_info
        assert (("mel_collecte", "test_entry_123")) in device_info.identifiers
        assert device_info.name == "Collectes MEL"
        assert device_info.manufacturer == "Publidata / MEL"
