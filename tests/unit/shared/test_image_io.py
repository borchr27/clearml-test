from pathlib import Path

import numpy as np
import pytest

from perception_template.shared.image_io import load_image


def test_load_image_roundtrip(tmp_path: Path) -> None:
    image = np.arange(12, dtype=np.uint8).reshape(3, 4)
    path = tmp_path / "image.npy"
    np.save(path, image)

    np.testing.assert_array_equal(load_image(path), image)


def test_load_image_rejects_unknown_extension(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unsupported"):
        load_image(tmp_path / "image.png")


def test_load_image_rejects_non_uint8(tmp_path: Path) -> None:
    path = tmp_path / "image.npy"
    np.save(path, np.zeros((2, 2), dtype=np.float32))

    with pytest.raises(ValueError, match="uint8"):
        load_image(path)
