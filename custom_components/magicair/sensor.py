"""Sensor platform for MagicAir and Tion 4S."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    CONCENTRATION_PARTS_PER_MILLION,
    PERCENTAGE,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from . import MagicAirConfigEntry
from .const import DEVICE_TYPE_BREEZER_4S, DEVICE_TYPE_STATION
from .entity import MagicAirEntity, iter_devices


@dataclass(frozen=True, kw_only=True)
class MagicAirSensorEntityDescription(SensorEntityDescription):
    """Describe a MagicAir sensor."""

    value_fn: Callable[[dict[str, Any]], int | float | str | None]


def _filter_remaining(device: dict[str, Any]) -> int | None:
    data = device.get("data", {})
    remaining = data.get("filter_time_seconds")
    used = data.get("run_seconds")
    if remaining is None or used is None:
        return None
    total = float(remaining) + float(used)
    if total <= 0:
        return None
    return round(max(0, min(100, float(remaining) / total * 100)))


STATION_SENSORS = (
    MagicAirSensorEntityDescription(
        key="co2",
        translation_key="co2",
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=CONCENTRATION_PARTS_PER_MILLION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda device: device.get("data", {}).get("co2"),
    ),
    MagicAirSensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
        value_fn=lambda device: device.get("data", {}).get("temperature"),
    ),
    MagicAirSensorEntityDescription(
        key="humidity",
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda device: device.get("data", {}).get("humidity"),
    ),
)

BREEZER_SENSORS = (
    MagicAirSensorEntityDescription(
        key="inlet_temperature",
        translation_key="inlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda device: device.get("data", {}).get("t_in"),
    ),
    MagicAirSensorEntityDescription(
        key="outlet_temperature",
        translation_key="outlet_temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        value_fn=lambda device: device.get("data", {}).get("t_out"),
    ),
    MagicAirSensorEntityDescription(
        key="filter_remaining",
        translation_key="filter_remaining",
        native_unit_of_measurement=PERCENTAGE,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_filter_remaining,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: MagicAirConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MagicAir sensors."""
    entities: list[MagicAirSensor] = []
    data = entry.runtime_data.coordinator.data
    for _, device in iter_devices(data, DEVICE_TYPE_STATION):
        entities.extend(
            MagicAirSensor(entry, device, description)
            for description in STATION_SENSORS
        )
    for _, device in iter_devices(data, DEVICE_TYPE_BREEZER_4S):
        entities.extend(
            MagicAirSensor(entry, device, description)
            for description in BREEZER_SENSORS
        )
    async_add_entities(entities)


class MagicAirSensor(MagicAirEntity, SensorEntity):
    """A sensor reported by the MagicAir cloud."""

    entity_description: MagicAirSensorEntityDescription

    def __init__(
        self,
        entry: MagicAirConfigEntry,
        device: dict[str, Any],
        description: MagicAirSensorEntityDescription,
    ) -> None:
        """Initialize a sensor."""
        super().__init__(entry, device)
        self.entity_description = description
        self._attr_unique_id = f"{device['guid']}_{description.key}"

    @property
    def native_value(self) -> int | float | str | None:
        """Return the current sensor value."""
        device = self.device
        return self.entity_description.value_fn(device) if device else None
