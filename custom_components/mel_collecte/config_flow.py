"""Config flow pour l'intégration MEL Collecte."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import callback

from .const import DEFAULT_INSTANCE_ID, DOMAIN


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


class MelCollecteOptionsFlow(config_entries.OptionsFlow):
    """Permet d'ajuster quelques paramètres (future extension)."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict | None = None):
        return self.async_abort(reason="not_supported")
