"""Number platform for Tion Breezer 4S."""

from __future__ import annotations

from typing import Any

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MagicAirConfigEntry
from .const import DEVICE_TYPE_BREEZER_4S
from .entity import MagicAirEntity, build_breezer_payload, iter_devices


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MagicAirConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up Tion 4S number entities."""
    async_add_entities(
        MagicAirTargetTemperature(entry, device)
        for _, device in iter_devices(
            entry.runtime_data.coordinator.data,
            DEVICE_TYPE_BREEZER_4S,
        )
    )


class MagicAirTargetTemperature(MagicAirEntity, NumberEntity):
    """Tion 4S heater target temperature."""

    _attr_translation_key = "target_temperature"
    _attr_icon = "mdi:thermometer"
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_mode = NumberMode.BOX

    def __init__(
        self,
        entry: MagicAirConfigEntry,
        device: dict[str, Any],
    ) -> None:
        """Initialize the target temperature entity."""
        super().__init__(entry, device)
        self._attr_unique_id = f"{device['guid']}_target_temperature"

    @property
    def native_min_value(self) -> float:
        """Return the minimum supported temperature."""
        return float((self.device or {}).get("t_min") or 0)

    @property
    def native_max_value(self) -> float:
        """Return the maximum supported temperature."""
        return float((self.device or {}).get("t_max") or 30)

    @property
    def native_value(self) -> float | None:
        """Return the configured temperature."""
        value = (self.device or {}).get("data", {}).get("t_set")
        return float(value) if value is not None else None

    async def async_set_native_value(self, value: float) -> None:
        """Set the target temperature."""
        device = self.device
        if not device:
            return
        await self.async_ensure_manual_mode()
        await self.coordinator.async_execute_device_command(
            self._device_id,
            "mode",
            build_breezer_payload(device, t_set=round(value)),
        )
