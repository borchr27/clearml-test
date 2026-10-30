"""Runs the whole application, as a user would, on a generated input image."""

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

REPO_ROOT = Path(__file__).resolve().parents[2]


def run_app(*args: str | Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "perception_template", *map(str, args)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
        check=False,
    )


def test_dark_image_is_flagged_with_repository_config(tmp_path: Path) -> None:
    image_path = tmp_path / "dark.npy"
    np.save(image_path, np.full((48, 64, 3), 10, dtype=np.uint8))

    completed = run_app(image_path)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["exposure"] == "dark"


def test_thresholds_are_read_from_config(tmp_path: Path) -> None:
    image_path = tmp_path / "grey.npy"
    np.save(image_path, np.full((48, 64), 128, dtype=np.uint8))
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "brightness_check:\n  dark_threshold: 0.6\n  bright_threshold: 0.9\n", encoding="utf-8"
    )

    completed = run_app(image_path, "--config", config_path)

    assert completed.returncode == 0, completed.stderr
    assert json.loads(completed.stdout)["exposure"] == "dark"
