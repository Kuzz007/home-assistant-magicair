"""Shared entities and state helpers for MagicAir."""

from __future__ import annotations

from typing import Any

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import MagicAirConfigEntry
from .const import (
    DEFAULT_CO2_TARGET,
    DEVICE_TYPE_BREEZER_4S,
    DEVICE_TYPE_STATION,
    DOMAIN,
    GATE_OUTSIDE_4S,
    HEATER_MODE_OFF,
    ZONE_MODE_AUTO,
    ZONE_MODE_MANUAL,
)
from .coordinator import MagicAirCoordinator

MODEL_NAMES = {
    DEVICE_TYPE_STATION: "MagicAir BS310",
    DEVICE_TYPE_BREEZER_4S: "Tion Breezer 4S",
}


def iter_devices(
    location: dict[str, Any],
    device_type: str | None = None,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Return (zone, device) pairs from a MagicAir location."""
    result: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for zone in location.get("zones", []):
        for device in zone.get("devices", []):
            if device_type is None or device.get("type") == device_type:
                result.append((zone, device))
    return result


def find_device(
    location: dict[str, Any],
    device_id: str,
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Find a device and its zone."""
    for zone, device in iter_devices(location):
        if device.get("guid") == device_id:
            return zone, device
    return None, None


def build_breezer_payload(
    device: dict[str, Any],
    **changes: Any,
) -> dict[str, Any]:
    """Build a complete Tion 4S mode command without resetting other fields."""
    data = device.get("data", {})
    max_speed = int(device.get("max_speed") or data.get("speed_limit") or 6)
    speed = int(changes.get("speed", data.get("speed") or 1))
    payload = {
        "is_on": bool(changes.get("is_on", data.get("is_on", False))),
        "speed": max(1, min(speed, max_speed)),
        "speed_min_set": int(data.get("speed_min_set") or 0),
        "speed_max_set": int(data.get("speed_max_set") or max_speed),
        "heater_mode": changes.get(
            "heater_mode",
            data.get("heater_mode", HEATER_MODE_OFF),
        ),
        "t_set": int(changes.get("t_set", data.get("t_set") or 20)),
        "gate": int(changes.get("gate", data.get("gate", GATE_OUTSIDE_4S))),
    }
    return payload


def get_zone_co2_target(zone: dict[str, Any]) -> int:
    """Return the configured automatic CO2 threshold."""
    try:
        target = int(zone["mode"]["auto_set"]["co2"])
    except (KeyError, TypeError, ValueError):
        return DEFAULT_CO2_TARGET
    return target if target > 0 else DEFAULT_CO2_TARGET


class MagicAirEntity(CoordinatorEntity[MagicAirCoordinator]):
    """Base class for entities attached to one MagicAir device."""

    _attr_has_entity_name = True

    def __init__(
        self,
        entry: MagicAirConfigEntry,
        device: dict[str, Any],
    ) -> None:
        """Initialize the entity."""
        super().__init__(entry.runtime_data.coordinator)
        self._entry = entry
        self._device_id = str(device["guid"])
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._device_id)},
            manufacturer="Tion",
            model=MODEL_NAMES.get(device.get("type"), str(device.get("type"))),
            name=str(
                device.get("name")
                or MODEL_NAMES.get(device.get("type"), "MagicAir")
            ),
            serial_number=device.get("serial_number") or None,
            sw_version=device.get("firmware") or None,
            hw_version=device.get("hardware") or None,
            configuration_url="https://magicair.tion.ru/dashboard/overview",
        )

    @property
    def device(self) -> dict[str, Any] | None:
        """Return the latest raw device state."""
        _, device = find_device(self.coordinator.data, self._device_id)
        return device

    @property
    def zone(self) -> dict[str, Any] | None:
        """Return the latest raw zone state."""
        zone, _ = find_device(self.coordinator.data, self._device_id)
        return zone

    @property
    def available(self) -> bool:
        """Return whether the cloud and device are available."""
        device = self.device
        return (
            super().available
            and device is not None
            and bool(device.get("is_online", False))
        )

    async def async_ensure_manual_mode(self) -> None:
        """Switch a zone to manual before changing a device setting."""
        zone = self.zone
        if (
            not zone
            or zone.get("mode", {}).get("current") != ZONE_MODE_AUTO
        ):
            return
        await self.coordinator.async_execute_zone_command(
            str(zone["guid"]),
            {
                "mode": ZONE_MODE_MANUAL,
                "co2": get_zone_co2_target(zone),
            },
        )
