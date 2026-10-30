import numpy as np
import pytest

from perception_template.brightness_check.check import Exposure, check_brightness
from perception_template.brightness_check.config import BrightnessCheckConfig

CONFIG = BrightnessCheckConfig(dark_threshold=0.2, bright_threshold=0.8)


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0, Exposure.DARK), (128, Exposure.OK), (255, Exposure.BRIGHT)],
)
def test_check_brightness_classifies_uniform_images(value: int, expected: Exposure) -> None:
    image = np.full((4, 4), value, dtype=np.uint8)

    result = check_brightness(image, CONFIG)

    assert result.exposure == expected
    assert result.mean_brightness == pytest.approx(value / 255)


def test_check_brightness_accepts_color_images() -> None:
    image = np.full((4, 4, 3), 128, dtype=np.uint8)

    assert check_brightness(image, CONFIG).exposure == Exposure.OK


def test_check_brightness_rejects_empty_image() -> None:
    with pytest.raises(ValueError, match="empty"):
        check_brightness(np.zeros((0, 0), dtype=np.uint8), CONFIG)
