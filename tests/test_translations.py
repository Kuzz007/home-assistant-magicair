"""Tests for MagicAir user-facing translations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TRANSLATIONS = (
    Path(__file__).parents[1]
    / "custom_components"
    / "magicair"
    / "translations"
)


def _load_translation(language: str) -> dict[str, Any]:
    return json.loads(
        (TRANSLATIONS / f"{language}.json").read_text(encoding="utf-8")
    )


def _leaf_paths(
    value: dict[str, Any],
    prefix: tuple[str, ...] = (),
) -> set[tuple[str, ...]]:
    paths: set[tuple[str, ...]] = set()
    for key, child in value.items():
        path = (*prefix, key)
        if isinstance(child, dict):
            paths.update(_leaf_paths(child, path))
        else:
            paths.add(path)
    return paths


def test_russian_translation_is_complete() -> None:
    """Every English user-facing string has a Russian equivalent."""
    english = _load_translation("en")
    russian = _load_translation("ru")

    assert _leaf_paths(russian) == _leaf_paths(english)


def test_fan_modes_are_translated_to_russian() -> None:
    """The raw normal/auto fan presets are presented in Russian."""
    russian = _load_translation("ru")
    modes = russian["entity"]["fan"]["breezer"]["state_attributes"][
        "preset_mode"
    ]["state"]

    assert modes == {
        "auto": "Автоматический",
        "normal": "Ручной",
    }
