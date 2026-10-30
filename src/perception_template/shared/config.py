"""Loading of the application config file (config.yaml)."""

from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path("config.yaml")


def load_config(path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    """Read the YAML config file and return its top-level mapping."""
    with path.open(encoding="utf-8") as file:
        data = yaml.safe_load(file) or {}
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping at the top level, got {type(data).__name__}")
    return data


def get_section(config: dict[str, Any], name: str) -> dict[str, Any]:
    """Return one top-level section of the config, or an empty mapping if it is missing."""
    section = config.get(name) or {}
    if not isinstance(section, dict):
        raise ValueError(f"config section '{name}' must be a mapping, got {type(section).__name__}")
    return section
