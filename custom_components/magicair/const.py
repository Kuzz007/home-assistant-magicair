"""Constants for the MagicAir integration."""

from __future__ import annotations

from typing import Final

DOMAIN: Final = "magicair"

CONF_LOCATION_ID: Final = "location_id"

API_BASE_URL: Final = "https://api2.magicair.tion.ru"
OAUTH_TOKEN_PATH: Final = "/idsrv/oauth2/token"
OAUTH_CLIENT_ID: Final = "a750d720-e146-47b0-b414-35e3b1dd7862"
OAUTH_CLIENT_SECRET: Final = "DTT2jJnY3k2H2GyZ"

DEFAULT_SCAN_INTERVAL: Final = 30
DEFAULT_REQUEST_TIMEOUT: Final = 15
DEFAULT_CO2_TARGET: Final = 800

DEVICE_TYPE_STATION: Final = "co2mb"
DEVICE_TYPE_BREEZER_4S: Final = "breezer4"

SUPPORTED_DEVICE_TYPES: Final = {
    DEVICE_TYPE_STATION,
    DEVICE_TYPE_BREEZER_4S,
}

PLATFORMS: Final = ["fan", "number", "sensor", "switch"]

PRESET_AUTO: Final = "auto"
PRESET_MANUAL: Final = "manual"

HEATER_MODE_ON: Final = "heat"
HEATER_MODE_OFF: Final = "maintenance"

GATE_OUTSIDE_4S: Final = 0
GATE_RECIRCULATION_4S: Final = 1
