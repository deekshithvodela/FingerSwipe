from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML


class ConfigurationError(ValueError):
    pass


@dataclass(slots=True, frozen=True)
class EngineConfig:
    dead_zone: float = 0.0
    smoothing: float = 1.0
    sensitivity: float = 1.0
    curve: str = "linear"
    axis_lock_threshold: float = 2.0


@dataclass(slots=True, frozen=True)
class VolumeConfig:
    enabled: bool = True
    axis: str = "vertical"
    minimum: float = 0.0
    maximum: float = 1.0
    step: float = 0.01
    threshold: float = 4.0


@dataclass(slots=True, frozen=True)
class BrightnessConfig:
    enabled: bool = True
    axis: str = "horizontal"
    minimum: float = 0.01
    maximum: float = 1.0
    step: float = 0.01
    threshold: float = 4.0


@dataclass(slots=True, frozen=True)
class TapConfig:
    enabled: bool = True
    max_distance: float = 4.0
    max_duration_ms: int = 1000
    action: str = "super_key"
    custom_command: str = ""


@dataclass(slots=True, frozen=True)
class LoggingConfig:
    level: str = "INFO"
    json: bool = False


@dataclass(slots=True, frozen=True)
class Config:
    engine: EngineConfig = EngineConfig()
    volume: VolumeConfig = VolumeConfig()
    brightness: BrightnessConfig = BrightnessConfig()
    tap: TapConfig = TapConfig()
    logging: LoggingConfig = LoggingConfig()


def default_config_path() -> Path:
    root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    return root / "fingerswipe" / "config.yaml"


def _section(data: dict[str, Any], name: str, allowed: set[str]) -> dict[str, Any]:
    raw = data.get(name, {})
    if not isinstance(raw, dict):
        raise ConfigurationError(f"{name} must be a mapping")
    unknown = set(raw) - allowed
    if unknown:
        raise ConfigurationError(f"unknown {name} keys: {', '.join(sorted(unknown))}")
    return raw


def load_config(path: Path | None = None) -> Config:
    target = path or default_config_path()
    if not target.exists():
        if path is not None:
            raise ConfigurationError(f"configuration file does not exist: {target}")
        return Config()
    try:
        raw = YAML(typ="safe").load(target) or {}
    except Exception as error:
        raise ConfigurationError(f"cannot parse {target}: {error}") from error
    if not isinstance(raw, dict):
        raise ConfigurationError("configuration root must be a mapping")
    unknown = set(raw) - {"engine", "volume", "brightness", "tap", "logging"}
    if unknown:
        raise ConfigurationError(f"unknown sections: {', '.join(sorted(unknown))}")
    try:
        engine = EngineConfig(**_section(raw, "engine", {"dead_zone", "smoothing", "sensitivity", "curve", "axis_lock_threshold"}))
        volume = VolumeConfig(**_section(raw, "volume", {"enabled", "axis", "minimum", "maximum", "step", "threshold"}))
        brightness = BrightnessConfig(**_section(raw, "brightness", {"enabled", "axis", "minimum", "maximum", "step", "threshold"}))
        tap = TapConfig(**_section(raw, "tap", {"enabled", "max_distance", "max_duration_ms", "action", "custom_command"}))
        logging = LoggingConfig(**_section(raw, "logging", {"level", "json"}))
    except TypeError as error:
        raise ConfigurationError(str(error)) from error
    if not 0.0 <= engine.dead_zone < 1.0:
        raise ConfigurationError("engine.dead_zone must be in [0, 1)")
    if not 0.0 < engine.smoothing <= 1.0:
        raise ConfigurationError("engine.smoothing must be in (0, 1]")
    if engine.sensitivity <= 0.0:
        raise ConfigurationError("engine.sensitivity must be positive")
    if engine.axis_lock_threshold <= 0.0:
        raise ConfigurationError("engine.axis_lock_threshold must be positive")
    if engine.curve not in {"linear", "power", "exponential"}:
        raise ConfigurationError("engine.curve must be linear, power, or exponential")

    if volume.axis not in {"vertical", "horizontal"}:
        raise ConfigurationError("volume.axis must be 'vertical' or 'horizontal'")
    if brightness.axis not in {"vertical", "horizontal"}:
        raise ConfigurationError("brightness.axis must be 'vertical' or 'horizontal'")

    if tap.max_distance <= 0.0:
        raise ConfigurationError("tap.max_distance must be positive")
    if tap.max_duration_ms <= 0:
        raise ConfigurationError("tap.max_duration_ms must be positive")
    if tap.action not in {"super_key", "custom_command"}:
        raise ConfigurationError("tap.action must be 'super_key' or 'custom_command'")

    if volume.enabled and brightness.enabled and volume.axis == brightness.axis:
        raise ConfigurationError("volume and brightness cannot be assigned to the same gesture axis")

    if not 0.0 <= volume.minimum <= volume.maximum <= 1.0:
        raise ConfigurationError("volume bounds must satisfy 0 <= minimum <= maximum <= 1")
    if not 0.0 < volume.step <= 1.0:
        raise ConfigurationError("volume.step must be in (0, 1]")
    if volume.threshold <= 0.0:
        raise ConfigurationError("volume.threshold must be positive")
    if not 0.0 <= brightness.minimum <= brightness.maximum <= 1.0:
        raise ConfigurationError("brightness bounds must satisfy 0 <= minimum <= maximum <= 1")
    if not 0.0 < brightness.step <= 1.0:
        raise ConfigurationError("brightness.step must be in (0, 1]")
    if brightness.threshold <= 0.0:
        raise ConfigurationError("brightness.threshold must be positive")
    if logging.level.upper() not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        raise ConfigurationError("logging.level is invalid")
    return Config(engine, volume, brightness, tap, LoggingConfig(logging.level.upper(), logging.json))
