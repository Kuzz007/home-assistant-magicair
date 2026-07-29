"""Diagnostics support for MagicAir."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.core import HomeAssistant

from . import MagicAirConfigEntry

TO_REDACT = {
    "access_token",
    "client_id",
    "client_secret",
    "guid",
    "mac",
    "mac_long",
    "password",
    "refresh_token",
    "serial_number",
    "unique_key",
    "user_guid",
    "username",
}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    entry: MagicAirConfigEntry,
) -> dict[str, Any]:
    """Return safely redacted diagnostics."""
    return {
        "entry": async_redact_data(dict(entry.data), TO_REDACT),
        "location": async_redact_data(
            entry.runtime_data.coordinator.data,
            TO_REDACT,
        ),
    }
