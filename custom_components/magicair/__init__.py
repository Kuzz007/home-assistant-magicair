"""MagicAir cloud integration."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MagicAirApi
from .const import CONF_LOCATION_ID, PLATFORMS
from .coordinator import MagicAirCoordinator


@dataclass(slots=True)
class MagicAirRuntimeData:
    """Runtime data for a MagicAir config entry."""

    api: MagicAirApi
    coordinator: MagicAirCoordinator


type MagicAirConfigEntry = ConfigEntry[MagicAirRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MagicAirConfigEntry,
) -> bool:
    """Set up MagicAir from a config entry."""
    api = MagicAirApi(
        async_get_clientsession(hass),
        entry.data[CONF_USERNAME],
        entry.data[CONF_PASSWORD],
    )
    coordinator = MagicAirCoordinator(
        hass,
        api,
        entry.data[CONF_LOCATION_ID],
    )
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = MagicAirRuntimeData(api=api, coordinator=coordinator)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: MagicAirConfigEntry,
) -> bool:
    """Unload a MagicAir config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
