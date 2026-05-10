"""Config flow pour l'intégration MEL Collecte."""

from __future__ import annotations

import asyncio
import voluptuous as vol
from aiohttp import ClientError
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MelCollecteAPI
from .const import (
    DEFAULT_INSTANCE_ID,
    DEFAULT_LOOKAHEAD_DAYS,
    DEFAULT_UPDATE_INTERVAL,
    DEFAULT_VISIBLE_TYPES,
    DOMAIN,
)


class MelCollecteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):  # type: ignore[call-arg]
    """Gestion du formulaire de configuration."""

    VERSION = 1

    async def async_step_user(self, user_input: dict | None = None):
        if user_input is None:
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema({vol.Required(CONF_ADDRESS): str}),
            )

        await self.async_set_unique_id(user_input[CONF_ADDRESS])
        self._abort_if_unique_id_configured()

        session = async_get_clientsession(self.hass)
        api = MelCollecteAPI(session)

        try:
            feature = await asyncio.wait_for(
                api.geocode_address(user_input[CONF_ADDRESS]), timeout=20
            )
        except asyncio.TimeoutError:
            return self.async_abort(reason="cannot_connect")
        except ClientError:
            return self.async_abort(reason="cannot_connect")

        if feature is None:
            return self.async_abort(reason="address_not_found")

        properties = feature.get("properties", {})
        address_id = properties.get("id")
        if not address_id:
            return self.async_abort(reason="outside_coverage")

        geometry = feature.get("geometry", {})
        coordinates = geometry.get("coordinates", [])
        lat = coordinates[1] if len(coordinates) >= 2 else None
        lon = coordinates[0] if len(coordinates) >= 2 else None

        try:
            collections = await asyncio.wait_for(
                api.fetch_waste_collections(
                    instance_id=DEFAULT_INSTANCE_ID,
                    address_id=address_id,
                    lat=lat,
                    lon=lon,
                ),
                timeout=20,
            )
        except asyncio.TimeoutError:
            return self.async_abort(reason="cannot_connect")
        except ClientError:
            return self.async_abort(reason="cannot_connect")

        if not collections:
            return self.async_abort(reason="outside_coverage")

        return self.async_create_entry(
            title=user_input[CONF_ADDRESS],
            data={
                "address": user_input[CONF_ADDRESS],
                "instance_id": DEFAULT_INSTANCE_ID,
            },
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return MelCollecteOptionsFlow(config_entry)


class MelCollecteOptionsFlow(config_entries.OptionsFlowWithConfigEntry):
    """Permet d'ajuster les paramètres de l'intégration."""

    async def async_step_init(self, user_input: dict | None = None):
        if user_input is not None:
            visible_types = user_input.get("visible_types", "")
            parsed_types = (
                [t.strip() for t in visible_types.split(",") if t.strip()]
                if visible_types
                else []
            )
            return self.async_create_entry(
                data={**user_input, "visible_types": parsed_types}
            )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "update_interval",
                        default=self.config_entry.options.get(
                            "update_interval", DEFAULT_UPDATE_INTERVAL
                        ),
                    ): int,
                    vol.Optional(
                        "lookahead_days",
                        default=self.config_entry.options.get(
                            "lookahead_days", DEFAULT_LOOKAHEAD_DAYS
                        ),
                    ): int,
                    vol.Optional(
                        "visible_types",
                        default=",".join(
                            self.config_entry.options.get(
                                "visible_types", DEFAULT_VISIBLE_TYPES
                            )
                        ),
                    ): str,
                }
            ),
        )
