"""Exposure classification of an image by its mean brightness."""

from dataclasses import dataclass
from enum import StrEnum

import numpy as np
from numpy.typing import NDArray

from perception_template.brightness_check.config import BrightnessCheckConfig


class Exposure(StrEnum):
    DARK = "dark"
    OK = "ok"
    BRIGHT = "bright"


@dataclass(frozen=True)
class BrightnessResult:
    mean_brightness: float  # 0.0 = black, 1.0 = white
    exposure: Exposure


def check_brightness(image: NDArray[np.uint8], config: BrightnessCheckConfig) -> BrightnessResult:
    """Classify an 8-bit image, shape (H, W) or (H, W, C), as dark, ok or bright."""
    if image.size == 0:
        raise ValueError("cannot check the brightness of an empty image")
    mean_brightness = float(image.mean()) / 255.0
    if mean_brightness < config.dark_threshold:
        exposure = Exposure.DARK
    elif mean_brightness > config.bright_threshold:
        exposure = Exposure.BRIGHT
    else:
        exposure = Exposure.OK
    return BrightnessResult(mean_brightness=mean_brightness, exposure=exposure)
