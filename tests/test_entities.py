"""Tests for MagicAir entity state helpers."""

from __future__ import annotations

from custom_components.magicair.const import (
    GATE_OUTSIDE_4S,
    HEATER_MODE_OFF,
    PLATFORMS,
)
from custom_components.magicair.entity import (
    build_breezer_payload,
    get_zone_co2_target,
    iter_devices,
)
from custom_components.magicair.fan import (
    _percentage_to_speed,
    _speed_to_percentage,
)
from custom_components.magicair.sensor import _filter_remaining


def test_build_breezer_payload_preserves_4s_state() -> None:
    """A one-field change must not reset other Tion 4S settings."""
    device = {
        "max_speed": 6,
        "data": {
            "is_on": True,
            "speed": 3,
            "speed_min_set": 0,
            "speed_max_set": 6,
            "heater_mode": "heat",
            "t_set": 23,
            "gate": 0,
        },
    }

    payload = build_breezer_payload(device, speed=5)

    assert payload == {
        "is_on": True,
        "speed": 5,
        "speed_min_set": 0,
        "speed_max_set": 6,
        "heater_mode": "heat",
        "t_set": 23,
        "gate": 0,
    }


def test_build_breezer_payload_has_safe_defaults() -> None:
    """Incomplete cloud data still produces a complete command."""
    payload = build_breezer_payload({"data": {}}, is_on=True)

    assert payload["is_on"] is True
    assert payload["speed"] == 1
    assert payload["heater_mode"] == HEATER_MODE_OFF
    assert payload["gate"] == GATE_OUTSIDE_4S


def test_filter_remaining() -> None:
    """Filter lifetime is returned as a clamped percentage."""
    assert (
        _filter_remaining(
            {
                "data": {
                    "filter_time_seconds": 75,
                    "run_seconds": 25,
                }
            }
        )
        == 75
    )
    assert _filter_remaining({"data": {}}) is None


def test_location_helpers() -> None:
    """Helpers identify devices and preserve an existing CO2 target."""
    station = {"guid": "station", "type": "co2mb"}
    zone = {
        "guid": "zone",
        "mode": {"auto_set": {"co2": 950}},
        "devices": [station],
    }
    location = {"zones": [zone]}

    assert iter_devices(location) == [(zone, station)]
    assert get_zone_co2_target(zone) == 950


def test_select_platform_is_loaded() -> None:
    """The explicit speed and operation controls are loaded."""
    assert "select" in PLATFORMS


def test_six_discrete_speeds_match_home_assistant_percentages() -> None:
    """Speed conversion stays reversible for all six Tion levels."""
    percentages = [16, 33, 50, 66, 83, 100]

    assert [
        _speed_to_percentage(speed, 6) for speed in range(1, 7)
    ] == percentages
    assert [
        _percentage_to_speed(percentage, 6) for percentage in percentages
    ] == list(range(1, 7))
