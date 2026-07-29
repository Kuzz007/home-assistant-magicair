"""Data coordinator for MagicAir."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Mapping
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntryAuthFailed
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import MagicAirApi, MagicAirAuthenticationError, MagicAirError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class MagicAirCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinate state updates and serialized commands."""

    def __init__(
        self,
        hass: HomeAssistant,
        api: MagicAirApi,
        location_id: str,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
            always_update=False,
        )
        self.api = api
        self.location_id = location_id
        self._command_lock = asyncio.Lock()

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            return await self.api.async_get_location(self.location_id)
        except MagicAirAuthenticationError as err:
            raise ConfigEntryAuthFailed from err
        except MagicAirError as err:
            raise UpdateFailed(str(err)) from err

    async def async_execute_device_command(
        self,
        device_id: str,
        command_type: str,
        payload: Mapping[str, Any],
    ) -> None:
        """Execute a device command, then refresh all entities."""
        async with self._command_lock:
            await self.api.async_execute_device_command(
                device_id,
                command_type,
                payload,
            )
            await self.async_request_refresh()

    async def async_execute_zone_command(
        self,
        zone_id: str,
        payload: Mapping[str, Any],
    ) -> None:
        """Execute a zone command, then refresh all entities."""
        async with self._command_lock:
            await self.api.async_execute_zone_command(zone_id, payload)
            await self.async_request_refresh()
