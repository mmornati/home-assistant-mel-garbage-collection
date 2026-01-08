"""Tests du coordinator."""

import asyncio
from datetime import datetime, timedelta, timezone
import pytest

from homeassistant.core import HomeAssistant

from custom_components.mel_collecte.coordinator import MelCollecteCoordinator


class DummyAPI:
    """Stubs API Publidata pour les tests."""

    async def geocode_address(self, address: str):
        return {
            "geometry": {"coordinates": [3.0, 50.0]},
            "properties": {"id": "ADDR_ID"},
        }

    async def fetch_waste_collections(self, **kwargs):
        return [
            {
                "id": "col_omr",
                "name": "Collecte OMR",
                "metas": {
                    "garbage_types": ["omr"],
                    "collection_mode": "door",
                },
                "schedules": [
                    {"opening_hours": "Th 13:15-20:15"},
                ],
            }
        ]

    async def fetch_alerts(self, **kwargs):
        return []


@pytest.mark.asyncio
async def test_coordinator_builds_events(monkeypatch):
    loop = asyncio.get_event_loop()
    hass = HomeAssistant(loop)
    api = DummyAPI()
    coordinator = MelCollecteCoordinator(
        hass,
        api,
        address="5 rue test",
        instance_id="876",
        lat=None,
        lon=None,
    )

    fixed_now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    fake_occurrence = {
        "start": fixed_now + timedelta(days=1),
        "end": fixed_now + timedelta(days=1, hours=1),
    }

    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.dt_util.utcnow",
        lambda: fixed_now,
    )
    monkeypatch.setattr(
        "custom_components.mel_collecte.coordinator.parse_schedule",
        lambda _schedule, _start, _end: [fake_occurrence],
    )

    data = await coordinator._async_update_data()

    assert data["collections"][0]["garbage_types_friendly"] == [
        "Ordures ménagères résiduelles"
    ]
    assert data["events"][0]["start"].tzinfo == timezone.utc
