from pathlib import Path

import pytest

from fingerswipe.config import ConfigurationError, Config, load_config


def test_missing_default_configuration_uses_defaults(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert load_config() == Config()


def test_complete_configuration_is_loaded(tmp_path: Path) -> None:
    path = tmp_path / "config.yaml"
    path.write_text("engine:\n  smoothing: 1.0\n  curve: power\nvolume:\n  maximum: 0.8\nlogging:\n  level: debug\n", encoding="utf-8")
    config = load_config(path)
    assert config.engine.curve == "power"
    assert config.volume.maximum == 0.8
    assert config.logging.level == "DEBUG"


@pytest.mark.parametrize("content", [
    "unknown: true\n", "engine:\n  smoothing: 0\n",
    "volume:\n  minimum: 0.9\n  maximum: 0.2\n", "engine: []\n",
])
def test_invalid_configuration_is_rejected(tmp_path: Path, content: str) -> None:
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_config(path)
