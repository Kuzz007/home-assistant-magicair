"""Select platform for Tion Breezer 4S."""

from __future__ import annotations

from typing import Any

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MagicAirConfigEntry
from .const import (
    DEVICE_TYPE_BREEZER_4S,
    ZONE_MODE_AUTO,
    ZONE_MODE_MANUAL,
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
    """Set up Tion 4S select entities."""
    entities: list[SelectEntity] = []
    for _, device in iter_devices(
        entry.runtime_data.coordinator.data,
        DEVICE_TYPE_BREEZER_4S,
    ):
        entities.extend(
            (
                MagicAirSpeedSelect(entry, device),
                MagicAirOperationModeSelect(entry, device),
            )
        )
    async_add_entities(entities)


class MagicAirSpeedSelect(MagicAirEntity, SelectEntity):
    """Select one of the Tion 4S discrete fan speeds."""

    _attr_translation_key = "fan_speed"
    _attr_icon = "mdi:fan"

    def __init__(
        self,
        entry: MagicAirConfigEntry,
        device: dict[str, Any],
    ) -> None:
        """Initialize the speed selector."""
        super().__init__(entry, device)
        self._attr_unique_id = f"{device['guid']}_fan_speed"
        max_speed = int(
            device.get("max_speed")
            or device.get("data", {}).get("speed_limit")
            or 6
        )
        self._attr_options = [str(speed) for speed in range(1, max_speed + 1)]

    @property
    def current_option(self) -> str | None:
        """Return the current discrete fan speed."""
        speed = (self.device or {}).get("data", {}).get("speed")
        try:
            option = str(int(speed)) if speed is not None else None
        except (TypeError, ValueError):
            return None
        return option if option in self.options else None

    async def async_select_option(self, option: str) -> None:
        """Set a discrete fan speed and switch to manual mode."""
        if option not in self.options:
            raise ValueError(f"Unsupported fan speed: {option}")
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
                speed=int(option),
            ),
        )


class MagicAirOperationModeSelect(MagicAirEntity, SelectEntity):
    """Select automatic or manual MagicAir zone operation."""

    _attr_translation_key = "operation_mode"
    _attr_icon = "mdi:autorenew"
    _attr_options = [ZONE_MODE_MANUAL, ZONE_MODE_AUTO]

    def __init__(
        self,
        entry: MagicAirConfigEntry,
        device: dict[str, Any],
    ) -> None:
        """Initialize the operation mode selector."""
        super().__init__(entry, device)
        self._attr_unique_id = f"{device['guid']}_operation_mode"

    @property
    def current_option(self) -> str | None:
        """Return the current MagicAir zone mode."""
        mode = (self.zone or {}).get("mode", {}).get("current")
        return mode if mode in self.options else None

    async def async_select_option(self, option: str) -> None:
        """Set automatic or manual MagicAir zone operation."""
        if option not in self.options:
            raise ValueError(f"Unsupported operation mode: {option}")
        zone = self.zone
        if not zone:
            return
        await self.coordinator.async_execute_zone_command(
            str(zone["guid"]),
            {
                "mode": option,
                "co2": get_zone_co2_target(zone),
            },
        )
