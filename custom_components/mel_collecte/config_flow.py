"""Config flow pour l'intégration MEL Collecte."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv

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
            return self.async_create_entry(data=user_input)

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
                        default=self.config_entry.options.get(
                            "visible_types", DEFAULT_VISIBLE_TYPES
                        ),
                    ): cv.ensure_list(cv.string),
                }
            ),
        )
