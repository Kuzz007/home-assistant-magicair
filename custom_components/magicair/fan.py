"""Fan platform for Tion Breezer 4S."""

from __future__ import annotations

import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MagicAirConfigEntry
from .const import (
    DEVICE_TYPE_BREEZER_4S,
    PRESET_AUTO,
    PRESET_MANUAL,
)
from .entity import (
    MagicAirEntity,
    build_breezer_payload,
    get_zone_co2_target,
    iter_devices,
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MagicAirConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Tion 4S fan entities."""
    async_add_entities(
        MagicAirBreezerFan(entry, device)
        for _, device in iter_devices(
            entry.runtime_data.coordinator.data,
            DEVICE_TYPE_BREEZER_4S,
        )
    )


class MagicAirBreezerFan(MagicAirEntity, FanEntity):
    """Representation of a Tion Breezer 4S."""

    _attr_name = None
    _attr_supported_features = (
        FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.SET_SPEED
        | FanEntityFeature.PRESET_MODE
    )
    _attr_preset_modes = [PRESET_MANUAL, PRESET_AUTO]

    def __init__(
        self,
        entry: MagicAirConfigEntry,
        device: dict[str, Any],
    ) -> None:
        """Initialize a Tion fan."""
        super().__init__(entry, device)
        self._attr_unique_id = f"{device['guid']}_fan"

    @property
    def is_on(self) -> bool:
        """Return whether the breezer is running."""
        return bool((self.device or {}).get("data", {}).get("is_on", False))

    @property
    def speed_count(self) -> int:
        """Return the number of discrete Tion speeds."""
        device = self.device or {}
        return int(
            device.get("max_speed")
            or device.get("data", {}).get("speed_limit")
            or 6
        )

    @property
    def percentage(self) -> int:
        """Return the current speed as a Home Assistant percentage."""
        if not self.is_on:
            return 0
        device = self.device or {}
        speed = int(device.get("data", {}).get("speed") or 1)
        return round(speed / self.speed_count * 100)

    @property
    def preset_mode(self) -> str | None:
        """Return automatic or manual zone mode."""
        mode = (self.zone or {}).get("mode", {}).get("current")
        return mode if mode in self.preset_modes else None

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the breezer on."""
        device = self.device
        if not device:
            return
        await self.async_ensure_manual_mode()
        changes: dict[str, Any] = {"is_on": True}
        if percentage is not None:
            changes["speed"] = self._percentage_to_speed(percentage)
        await self.coordinator.async_execute_device_command(
            self._device_id,
            "mode",
            build_breezer_payload(device, **changes),
        )
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the breezer off."""
        device = self.device
        if not device:
            return
        await self.async_ensure_manual_mode()
        await self.coordinator.async_execute_device_command(
            self._device_id,
            "mode",
            build_breezer_payload(device, is_on=False),
        )

    async def async_set_percentage(self, percentage: int) -> None:
        """Set a Tion discrete speed using a Home Assistant percentage."""
        if percentage <= 0:
            await self.async_turn_off()
            return
        device = self.device
        if not device:
            return
        await self.async_ensure_manual_mode()
        await self.coordinator.async_execute_device_command(
            self._device_id,
            "mode",
            build_breezer_payload(
                device,
                is_on=True,
                speed=self._percentage_to_speed(percentage),
            ),
        )

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Set automatic or manual operation for the breezer zone."""
        if preset_mode not in self.preset_modes:
            raise ValueError(f"Unsupported preset mode: {preset_mode}")
        zone = self.zone
        if not zone:
            return
        await self.coordinator.async_execute_zone_command(
            str(zone["guid"]),
            {
                "mode": preset_mode,
                "co2": get_zone_co2_target(zone),
            },
        )

    def _percentage_to_speed(self, percentage: int) -> int:
        return max(
            1,
            min(self.speed_count, math.ceil(percentage / 100 * self.speed_count)),
        )
