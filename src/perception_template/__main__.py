"""Application entry point: `pixi run start <image.npy>` or `python -m perception_template`."""

import argparse
import json
import logging
from pathlib import Path

from perception_template.brightness_check import BrightnessCheckConfig, check_brightness
from perception_template.shared.config import DEFAULT_CONFIG_PATH, get_section, load_config
from perception_template.shared.image_io import load_image
from perception_template.shared.log import setup_logging

logger = logging.getLogger(__name__)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="perception-template", description=__doc__)
    parser.add_argument("image", type=Path, help="input image (.npy, uint8)")
    parser.add_argument(
        "--config", type=Path, default=DEFAULT_CONFIG_PATH, help="path to the config file"
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    config = load_config(args.config)
    setup_logging(get_section(config, "app").get("log_level", "INFO"))

    brightness_config = BrightnessCheckConfig.from_dict(get_section(config, "brightness_check"))
    image = load_image(args.image)
    logger.info("Checking brightness of %s (shape %s)", args.image, image.shape)
    result = check_brightness(image, brightness_config)

    print(json.dumps({"mean_brightness": result.mean_brightness, "exposure": result.exposure}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
