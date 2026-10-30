from pathlib import Path

import pytest

from perception_template.shared.config import get_section, load_config


def test_load_config_reads_mapping(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("app:\n  log_level: DEBUG\n", encoding="utf-8")

    assert load_config(path) == {"app": {"log_level": "DEBUG"}}


def test_load_config_empty_file_is_empty_mapping(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("", encoding="utf-8")

    assert load_config(path) == {}


def test_load_config_rejects_non_mapping(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("- a\n- b\n", encoding="utf-8")

    with pytest.raises(ValueError, match="mapping"):
        load_config(path)


def test_get_section_missing_is_empty() -> None:
    assert get_section({}, "app") == {}


def test_get_section_rejects_non_mapping() -> None:
    with pytest.raises(ValueError, match="app"):
        get_section({"app": 3}, "app")
