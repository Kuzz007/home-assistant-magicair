"""Config flow for MagicAir."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import ConfigFlowResult
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    MagicAirApi,
    MagicAirAuthenticationError,
    MagicAirConnectionError,
    MagicAirError,
)
from .const import CONF_LOCATION_ID, DOMAIN


def _credentials_schema(
    defaults: dict[str, Any] | None = None,
) -> vol.Schema:
    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(
                CONF_USERNAME,
                default=defaults.get(CONF_USERNAME, ""),
            ): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.EMAIL)
            ),
            vol.Required(CONF_PASSWORD): selector.TextSelector(
                selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
            ),
        }
    )


class MagicAirConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a MagicAir config flow."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._pending_credentials: dict[str, str] = {}
        self._locations: dict[str, str] = {}

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Collect and validate MagicAir account credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                locations = await self._async_validate_credentials(user_input)
            except MagicAirAuthenticationError:
                errors["base"] = "invalid_auth"
            except MagicAirConnectionError:
                errors["base"] = "cannot_connect"
            except MagicAirError:
                errors["base"] = "unknown"
            else:
                if not locations:
                    errors["base"] = "no_locations"
                else:
                    self._pending_credentials = {
                        CONF_USERNAME: user_input[CONF_USERNAME],
                        CONF_PASSWORD: user_input[CONF_PASSWORD],
                    }
                    self._locations = {
                        str(location["guid"]): str(
                            location.get("name") or location["guid"]
                        )
                        for location in locations
                        if location.get("guid")
                    }
                    if len(self._locations) == 1:
                        location_id = next(iter(self._locations))
                        return await self._async_create_location_entry(location_id)
                    return await self.async_step_location()

        return self.async_show_form(
            step_id="user",
            data_schema=_credentials_schema(user_input),
            errors=errors,
        )

    async def async_step_location(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Let the user choose a home when the account has several."""
        if not self._locations or not self._pending_credentials:
            return self.async_abort(reason="missing_credentials")

        if user_input is not None:
            return await self._async_create_location_entry(
                user_input[CONF_LOCATION_ID]
            )

        return self.async_show_form(
            step_id="location",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_LOCATION_ID): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=[
                                selector.SelectOptionDict(value=guid, label=name)
                                for guid, name in self._locations.items()
                            ],
                            mode=selector.SelectSelectorMode.DROPDOWN,
                        )
                    )
                }
            ),
        )

    async def async_step_reauth(
        self,
        entry_data: dict[str, Any],
    ) -> ConfigFlowResult:
        """Start reauthentication."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> ConfigFlowResult:
        """Validate replacement credentials."""
        reauth_entry = self._get_reauth_entry()
        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                locations = await self._async_validate_credentials(user_input)
            except MagicAirAuthenticationError:
                errors["base"] = "invalid_auth"
            except MagicAirConnectionError:
                errors["base"] = "cannot_connect"
            except MagicAirError:
                errors["base"] = "unknown"
            else:
                location_id = reauth_entry.data[CONF_LOCATION_ID]
                if not any(
                    location.get("guid") == location_id for location in locations
                ):
                    errors["base"] = "location_missing"
                else:
                    return self.async_update_reload_and_abort(
                        reauth_entry,
                        data_updates={
                            CONF_USERNAME: user_input[CONF_USERNAME],
                            CONF_PASSWORD: user_input[CONF_PASSWORD],
                        },
                    )

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=_credentials_schema(
                {CONF_USERNAME: reauth_entry.data[CONF_USERNAME]}
            ),
            errors=errors,
        )

    async def _async_validate_credentials(
        self,
        user_input: dict[str, Any],
    ) -> list[dict[str, Any]]:
        api = MagicAirApi(
            async_get_clientsession(self.hass),
            user_input[CONF_USERNAME],
            user_input[CONF_PASSWORD],
        )
        return await api.async_get_locations()

    async def _async_create_location_entry(
        self, location_id: str
    ) -> ConfigFlowResult:
        await self.async_set_unique_id(location_id)
        self._abort_if_unique_id_configured()
        return self.async_create_entry(
            title=self._locations[location_id],
            data={
                **self._pending_credentials,
                CONF_LOCATION_ID: location_id,
            },
        )
