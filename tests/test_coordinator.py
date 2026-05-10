"""Tests du coordinator - scénarios avancés."""

import asyncio
from datetime import datetime, timedelta, timezone
import pytest

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.mel_collecte.coordinator import MelCollecteCoordinator


class DummyAPI:
    """API factice avec réponses configurables."""

    _default_geocode = {
        "geometry": {"coordinates": [3.0, 50.0]},
        "properties": {"id": "ADDR_ID"},
    }
    _default_collections = []
    _default_alerts = []

    def __init__(
        self, geocode_result=None, collections_result=None, alerts_result=None
    ):
        self._geocode_result = (
            geocode_result if geocode_result is not None else self._default_geocode
        )
        self._collections_result = (
            collections_result
            if collections_result is not None
            else self._default_collections
        )
        self._alerts_result = (
            alerts_result if alerts_result is not None else self._default_alerts
        )
        self.geocode_call_count = 0
        self.collections_call_count = 0
        self.alerts_call_count = 0

    async def geocode_address(self, address: str):
        self.geocode_call_count += 1
        return self._geocode_result

    async def fetch_waste_collections(self, **kwargs):
        self.collections_call_count += 1
        return self._collections_result

    async def fetch_alerts(self, **kwargs):
        self.alerts_call_count += 1
        return self._alerts_result


@pytest.mark.asyncio
async def test_coordinator_caches_geocode(monkeypatch):
    """Le coordinator met en cache le geocode et ne refait pas l'appel."""
    api = DummyAPI()
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address="5 rue test",
        instance_id="876",
        lat=None,
        lon=None,
    )

    fixed_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.dt_util.utcnow",
        lambda: fixed_now,
    )
    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.parse_schedule",
        lambda _s, _st, _e: [],
    )

    await coordinator._async_update_data()
    first_call_count = api.geocode_call_count

    await coordinator._async_update_data()
    second_call_count = api.geocode_call_count

    assert first_call_count == 1
    assert second_call_count == 1


@pytest.mark.asyncio
async def test_coordinator_raises_on_none_geocode(monkeypatch):
    """Le coordinator lève UpdateFailed quand geocode retourne None."""
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)

    class NoneAPI:
        async def geocode_address(self, address):
            return None

        async def fetch_waste_collections(self, **kwargs):
            return []

        async def fetch_alerts(self, **kwargs):
            return []

    coordinator = MelCollecteCoordinator(
        hass,
        NoneAPI(),
        address="invalid address",
        instance_id="876",
        lat=None,
        lon=None,
    )

    fixed_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.dt_util.utcnow",
        lambda: fixed_now,
    )

    try:
        await coordinator._async_update_data()
        assert False, "Expected UpdateFailed was not raised"
    except UpdateFailed as e:
        assert "introuvable" in str(e).lower() or "adresse" in str(e).lower()


@pytest.mark.asyncio
async def test_coordinator_raises_update_failed_on_invalid_coordinates():
    """Si les coordonnées sont invalides, UpdateFailed est levée."""
    api = DummyAPI(geocode_result={"geometry": {}, "properties": {"id": "ADDR_ID"}})
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address="5 rue test",
        instance_id="876",
        lat=None,
        lon=None,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_raises_update_failed_on_missing_address_id():
    """Si address_id est manquant, UpdateFailed est levée."""
    api = DummyAPI(
        geocode_result={"geometry": {"coordinates": [3.0, 50.0]}, "properties": {}}
    )
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address="5 rue test",
        instance_id="876",
        lat=None,
        lon=None,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_raises_update_failed_on_api_error():
    """Si l'API lève une exception, UpdateFailed est levée."""

    class FailingAPI:
        async def geocode_address(self, address):
            raise Exception("Network error")

    api = FailingAPI()
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address="5 rue test",
        instance_id="876",
        lat=None,
        lon=None,
    )

    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()


@pytest.mark.asyncio
async def test_coordinator_uses_explicit_lat_lon(monkeypatch):
    """Si lat/lon sont fournis, ils sont utilisés plutôt que ceux du geocode."""
    api = DummyAPI(
        geocode_result={
            "geometry": {"coordinates": [10.0, 60.0]},
            "properties": {"id": "ADDR_ID"},
        }
    )
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address="5 rue test",
        instance_id="876",
        lat=50.6,
        lon=3.0,
    )

    fixed_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.dt_util.utcnow",
        lambda: fixed_now,
    )
    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.parse_schedule",
        lambda _s, _st, _e: [
            {
                "start": fixed_now + timedelta(days=1),
                "end": fixed_now + timedelta(days=1, hours=1),
            }
        ],
    )

    await coordinator._async_update_data()

    assert coordinator.lat == 50.6
    assert coordinator.lon == 3.0


@pytest.mark.asyncio
async def test_coordinator_handles_empty_collections(monkeypatch):
    """Le coordinator gère les collections vides."""
    api = DummyAPI(collections_result=[])
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address="5 rue test",
        instance_id="876",
        lat=None,
        lon=None,
    )

    fixed_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.dt_util.utcnow",
        lambda: fixed_now,
    )

    data = await coordinator._async_update_data()

    assert data["collections"] == []
    assert data["events"] == []


@pytest.mark.asyncio
async def test_coordinator_handles_empty_alerts(monkeypatch):
    """Le coordinator gère les alertes vides."""
    api = DummyAPI(collections_result=[], alerts_result=[])
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address="5 rue test",
        instance_id="876",
        lat=None,
        lon=None,
    )

    fixed_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.dt_util.utcnow",
        lambda: fixed_now,
    )

    data = await coordinator._async_update_data()

    assert data["alerts"] == []


@pytest.mark.asyncio
async def test_coordinator_parses_multiple_occurrences(monkeypatch):
    """Le coordinator parse plusieurs occurrences d'une même collecte."""
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    api = DummyAPI(
        collections_result=[
            {
                "id": "col_1",
                "name": "Collecte OMR",
                "metas": {"garbage_types": ["omr"], "collection_mode": "door"},
                "schedules": [
                    {"opening_hours": "Th 05:50-12:50"},
                ],
            }
        ]
    )
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address="5 rue test",
        instance_id="876",
        lat=None,
        lon=None,
    )

    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.dt_util.utcnow",
        lambda: now,
    )

    def mock_parse(schedule, start, end):
        return [
            {
                "start": now + timedelta(days=i * 7),
                "end": now + timedelta(days=i * 7, hours=1),
            }
            for i in range(4)
        ]

    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.parse_schedule",
        mock_parse,
    )

    data = await coordinator._async_update_data()

    assert len(data["events"]) == 4
    assert data["collections"][0]["garbage_types_friendly"] == [
        "Ordures ménagères résiduelles"
    ]


@pytest.mark.asyncio
async def test_coordinator_sorts_events_by_start_time(monkeypatch):
    """Les événements sont triés par date de début."""
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    api = DummyAPI(
        collections_result=[
            {
                "id": "col_1",
                "name": "Collecte OMR",
                "metas": {"garbage_types": ["omr"], "collection_mode": "door"},
                "schedules": [{"opening_hours": "Th 05:50-12:50"}],
            }
        ]
    )
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)

    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address="5 rue test",
        instance_id="876",
        lat=None,
        lon=None,
    )

    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.dt_util.utcnow",
        lambda: now,
    )

    def mock_parse(schedule, start, end):
        return [
            {
                "start": now + timedelta(days=10),
                "end": now + timedelta(days=10, hours=1),
            },
            {"start": now + timedelta(days=3), "end": now + timedelta(days=3, hours=1)},
            {"start": now + timedelta(days=7), "end": now + timedelta(days=7, hours=1)},
        ]

    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.parse_schedule",
        mock_parse,
    )

    data = await coordinator._async_update_data()

    event_starts = [evt["start"] for evt in data["events"]]
    assert event_starts == sorted(event_starts)
