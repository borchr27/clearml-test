"""Config of the brightness_check feature (the `brightness_check` section of config.yaml)."""

from dataclasses import dataclass, fields
from typing import Any, Self


@dataclass(frozen=True)
class BrightnessCheckConfig:
    dark_threshold: float = 0.2
    bright_threshold: float = 0.8

    def __post_init__(self) -> None:
        if not 0.0 <= self.dark_threshold < self.bright_threshold <= 1.0:
            raise ValueError(
                "brightness_check: expected 0 <= dark_threshold < bright_threshold <= 1, got "
                f"dark_threshold={self.dark_threshold}, bright_threshold={self.bright_threshold}"
            )

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Self:
        known = {field.name for field in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"brightness_check: unknown config keys {sorted(unknown)}")
        return cls(**data)
