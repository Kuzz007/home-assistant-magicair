"""Smoke tests against the supported Home Assistant version."""

from __future__ import annotations

import importlib

import pytest

MODULES = (
    "custom_components.magicair",
    "custom_components.magicair.api",
    "custom_components.magicair.config_flow",
    "custom_components.magicair.coordinator",
    "custom_components.magicair.diagnostics",
    "custom_components.magicair.entity",
    "custom_components.magicair.fan",
    "custom_components.magicair.number",
    "custom_components.magicair.sensor",
    "custom_components.magicair.switch",
)


@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module: str) -> None:
    """Every integration module imports with the supported HA API."""
    assert importlib.import_module(module)
