"""Reading images from disk."""

from pathlib import Path

import numpy as np
from numpy.typing import NDArray


def load_image(path: Path) -> NDArray[np.uint8]:
    """Load an 8-bit image stored as a NumPy array (.npy), shape (H, W) or (H, W, C)."""
    if path.suffix != ".npy":
        raise ValueError(f"{path}: unsupported image format '{path.suffix}', expected .npy")
    image = np.load(path)
    if image.dtype != np.uint8 or image.ndim not in (2, 3):
        raise ValueError(f"{path}: expected a uint8 array of shape (H, W) or (H, W, C)")
    return image
