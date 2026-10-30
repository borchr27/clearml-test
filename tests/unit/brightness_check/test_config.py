import pytest

from perception_template.brightness_check.config import BrightnessCheckConfig


def test_from_dict_uses_defaults_for_missing_keys() -> None:
    assert BrightnessCheckConfig.from_dict({}) == BrightnessCheckConfig()


def test_from_dict_rejects_unknown_keys() -> None:
    with pytest.raises(ValueError, match="unknown"):
        BrightnessCheckConfig.from_dict({"threshold": 0.5})


@pytest.mark.parametrize(("dark", "bright"), [(0.8, 0.2), (0.5, 0.5), (-0.1, 0.5), (0.5, 1.1)])
def test_rejects_invalid_thresholds(dark: float, bright: float) -> None:
    with pytest.raises(ValueError, match="threshold"):
        BrightnessCheckConfig(dark_threshold=dark, bright_threshold=bright)
