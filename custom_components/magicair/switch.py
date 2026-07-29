"""Switch platform for MagicAir and Tion 4S."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from homeassistant.components.switch import SwitchEntity, SwitchEntityDescription
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MagicAirConfigEntry
from .const import (
    DEVICE_TYPE_BREEZER_4S,
    DEVICE_TYPE_STATION,
    GATE_OUTSIDE_4S,
    GATE_RECIRCULATION_4S,
    HEATER_MODE_OFF,
    HEATER_MODE_ON,
)
from .entity import MagicAirEntity, build_breezer_payload, iter_devices


@dataclass(frozen=True, kw_only=True)
class MagicAirSwitchEntityDescription(SwitchEntityDescription):
    """Describe a MagicAir switch."""


HEATER_DESCRIPTION = MagicAirSwitchEntityDescription(
    key="heater",
    translation_key="heater",
    icon="mdi:radiator",
)

RECIRCULATION_DESCRIPTION = MagicAirSwitchEntityDescription(
    key="recirculation",
    translation_key="recirculation",
    icon="mdi:air-filter",
)

BACKLIGHT_DESCRIPTION = MagicAirSwitchEntityDescription(
    key="backlight",
    translation_key="backlight",
    icon="mdi:lightbulb-outline",
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MagicAirConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MagicAir switches."""
    entities: list[SwitchEntity] = []
    data = entry.runtime_data.coordinator.data
    for _, device in iter_devices(data, DEVICE_TYPE_BREEZER_4S):
        entities.extend(
            (
                MagicAirHeaterSwitch(entry, device),
                MagicAirRecirculationSwitch(entry, device),
            )
        )
    for _, device in iter_devices(data, DEVICE_TYPE_STATION):
        entities.append(MagicAirBacklightSwitch(entry, device))
    async_add_entities(entities)


class MagicAirSwitch(MagicAirEntity, SwitchEntity):
    """Base class for MagicAir switches."""

    def __init__(
        self,
        entry: MagicAirConfigEntry,
        device: dict[str, Any],
        description: MagicAirSwitchEntityDescription,
    ) -> None:
        """Initialize a switch."""
        super().__init__(entry, device)
        self.entity_description = description
        self._attr_unique_id = f"{device['guid']}_{description.key}"


class MagicAirHeaterSwitch(MagicAirSwitch):
    """Control the Tion 4S heater."""

    def __init__(
        self,
        entry: MagicAirConfigEntry,
        device: dict[str, Any],
    ) -> None:
        """Initialize the heater switch."""
        super().__init__(entry, device, HEATER_DESCRIPTION)

    @property
    def is_on(self) -> bool:
        """Return whether heater mode is enabled."""
        return (
            (self.device or {}).get("data", {}).get("heater_mode")
            == HEATER_MODE_ON
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable heating."""
        await self._async_set_heater(HEATER_MODE_ON)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable heating."""
        await self._async_set_heater(HEATER_MODE_OFF)

    async def _async_set_heater(self, mode: str) -> None:
        device = self.device
        if not device:
            return
        await self.async_ensure_manual_mode()
        await self.coordinator.async_execute_device_command(
            self._device_id,
            "mode",
            build_breezer_payload(device, heater_mode=mode),
        )


class MagicAirRecirculationSwitch(MagicAirSwitch):
    """Control the Tion 4S recirculation gate."""

    def __init__(
        self,
        entry: MagicAirConfigEntry,
        device: dict[str, Any],
    ) -> None:
        """Initialize the recirculation switch."""
        super().__init__(entry, device, RECIRCULATION_DESCRIPTION)

    @property
    def is_on(self) -> bool:
        """Return whether recirculation is active."""
        return (
            (self.device or {}).get("data", {}).get("gate")
            == GATE_RECIRCULATION_4S
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable recirculation."""
        await self._async_set_gate(GATE_RECIRCULATION_4S)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Use outside air."""
        await self._async_set_gate(GATE_OUTSIDE_4S)

    async def _async_set_gate(self, gate: int) -> None:
        device = self.device
        if not device:
            return
        await self.async_ensure_manual_mode()
        changes: dict[str, Any] = {"gate": gate}
        if gate == GATE_RECIRCULATION_4S:
            changes["heater_mode"] = HEATER_MODE_OFF
        await self.coordinator.async_execute_device_command(
            self._device_id,
            "mode",
            build_breezer_payload(device, **changes),
        )


class MagicAirBacklightSwitch(MagicAirSwitch):
    """Control the BS310 indicator backlight."""

    def __init__(
        self,
        entry: MagicAirConfigEntry,
        device: dict[str, Any],
    ) -> None:
        """Initialize the backlight switch."""
        super().__init__(entry, device, BACKLIGHT_DESCRIPTION)

    @property
    def is_on(self) -> bool:
        """Return whether the station backlight is on."""
        return bool((self.device or {}).get("data", {}).get("backlight", 0))

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the station backlight on."""
        await self._async_set_backlight(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the station backlight off."""
        await self._async_set_backlight(False)

    async def _async_set_backlight(self, enabled: bool) -> None:
        await self.coordinator.async_execute_device_command(
            self._device_id,
            "settings",
            {"backlight": 1 if enabled else 0},
        )
