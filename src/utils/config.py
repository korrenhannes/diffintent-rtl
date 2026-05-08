from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import yaml

from src.utils.io import ensure_dir


def load_yaml_config(path: Path | str) -> dict[str, Any]:
    """Load a YAML config file into a dictionary."""

    with Path(path).open("r", encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    if not isinstance(payload, dict):
        raise TypeError(f"Config at {path} must be a mapping.")
    return payload


def deep_update(base: dict[str, Any], update: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge two configuration dictionaries."""

    merged = copy.deepcopy(base)
    for key, value in update.items():
        if (
            key in merged
            and isinstance(merged[key], dict)
            and isinstance(value, dict)
        ):
            merged[key] = deep_update(merged[key], value)
        else:
            merged[key] = copy.deepcopy(value)
    return merged


def load_and_merge_configs(*paths: Path | str) -> dict[str, Any]:
    """Load multiple YAML files and merge them in order."""

    merged: dict[str, Any] = {}
    for path in paths:
        merged = deep_update(merged, load_yaml_config(path))
    return merged


def save_yaml_config(config: dict[str, Any], path: Path | str) -> None:
    """Persist a YAML config for reproducibility."""

    path_obj = Path(path)
    ensure_dir(path_obj.parent)
    with path_obj.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(config, handle, sort_keys=False)

