"""Tests pour les événements et services dans __init__.py."""

from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta, timezone

import pytest

from custom_components.mel_collecte import async_setup_entry, async_unload_entry
from custom_components.mel_collecte.const import DOMAIN, EVENT_COLLECTION_UPCOMING


@pytest.mark.asyncio
async def test_async_setup_entry_registers_services_and_fires_events():
    """Test setup entry registers services and correctly fires the upcoming event."""
    hass = MagicMock()
    hass.data = {}

    # Mock services
    hass.services.async_register = MagicMock()
    hass.services.async_remove = MagicMock()

    # Mock config entries
    hass.config_entries.async_forward_entry_setups = AsyncMock(return_value=True)
    hass.config_entries.async_unload_platforms = AsyncMock(return_value=True)

    # Mock bus
    hass.bus.async_fire = MagicMock()

    entry = MagicMock()
    entry.entry_id = "test_entry"
    entry.data = {"address": "Test Address", "instance_id": "123"}
    entry.options = {}

    now = datetime(2025, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    # Event starting in 12 hours (offset is default 24, so it should fire)
    event_start = now + timedelta(hours=12)

    with patch(
        "custom_components.mel_collecte.api.MelCollecteAPI"
    ) as mock_api_cls, patch(
        "custom_components.mel_collecte.__init__.MelCollecteCoordinator.async_config_entry_first_refresh",
        new_callable=AsyncMock,
        create=True,
    ) as _mock_refresh, patch(
        "custom_components.mel_collecte.__init__.MelCollecteCoordinator.async_add_listener",
        create=True,
    ) as mock_add_listener, patch(
        "homeassistant.util.dt.utcnow", return_value=now
    ):

        mock_api_cls.return_value = MagicMock()

        hass.async_create_task = AsyncMock()

        result = await async_setup_entry(hass, entry)
        assert result is True

        assert hass.services.async_register.call_count == 2

        coordinator = hass.data[DOMAIN]["test_entry"]["coordinator"]

        coordinator.data = {
            "events": [
                {
                    "collection_id": "col_1",
                    "garbage_types": ["omr"],
                    "garbage_types_friendly": ["OMR"],
                    "start": event_start,
                    "end": event_start + timedelta(hours=1),
                    "name": "Collecte OMR",
                }
            ]
        }

        # Trigger the listener manually using the captured callback
        listener = mock_add_listener.call_args[0][0]

        import inspect

        if inspect.iscoroutinefunction(listener):
            await listener()
        else:
            listener()

        if hass.async_create_task.called:
            scheduled_coro = hass.async_create_task.call_args[0][0]
            await scheduled_coro

        assert hass.bus.async_fire.call_count == 1
        args, kwargs = hass.bus.async_fire.call_args
        assert args[0] == f"{DOMAIN}.{EVENT_COLLECTION_UPCOMING}"
        assert args[1]["collection_id"] == "col_1"
        assert args[1]["hours_until"] == 12

        # Call it again to test that it doesn't fire twice
        hass.async_create_task.reset_mock()
        if inspect.iscoroutinefunction(listener):
            await listener()
        else:
            listener()

        if hass.async_create_task.called:
            scheduled_coro = hass.async_create_task.call_args[0][0]
            await scheduled_coro

        assert hass.bus.async_fire.call_count == 1

        unload_result = await async_unload_entry(hass, entry)
        assert unload_result is True
        assert hass.services.async_remove.call_count == 2
