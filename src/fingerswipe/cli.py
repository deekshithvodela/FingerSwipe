from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path
from typing import Any

from fingerswipe.app import Application
from fingerswipe.version import __version__
from fingerswipe.backends.brightness import NativeBrightnessBackend
from fingerswipe.backends.pipewire import PipeWireBackend
from ruamel.yaml import YAML
from fingerswipe.config import BrightnessConfig, Config, ConfigurationError, TapConfig, VolumeConfig, load_config
from fingerswipe.controllers.brightness import BrightnessController
from fingerswipe.controllers.router import GestureAxisRouter
from fingerswipe.controllers.tap import TapController
from fingerswipe.controllers.volume import VolumeController
from fingerswipe.curves.exponential import ExponentialCurve
from fingerswipe.curves.linear import LinearCurve
from fingerswipe.curves.power import PowerCurve
from fingerswipe.engine.processor import GestureEngine
from fingerswipe.logger import configure_logging
from fingerswipe.native import NativeError, load_native
from fingerswipe.providers.libinput import LibinputProvider
from fingerswipe.providers.raw_mt import Raw4FingerTapDetector
from fingerswipe.eligibility import run_eligibility_checks, print_eligibility_report


def main() -> None:
    # Handle backward compatibility: default to "run" if no subcommand is provided
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] not in ("check", "run", "config", "gui", "-h", "--help", "-v", "--version")):
        sys.argv.insert(1, "run")

    parser = argparse.ArgumentParser(description="Control volume and brightness with three-finger swipes")
    parser.add_argument("-v", "--version", action="version", version=f"FingerSwipe {__version__}")
    subparsers = parser.add_subparsers(dest="command", help="subcommands")

    # 'run' subcommand
    run_parser = subparsers.add_parser("run", help="run the gestures controller service")
    run_parser.add_argument("--config", type=Path, help="configuration file")
    run_parser.add_argument("--library", type=Path, help="native shared library")

    volume_group = run_parser.add_mutually_exclusive_group()
    volume_group.add_argument("--enable-volume", action="store_true", default=None, help="enable volume control")
    volume_group.add_argument("--disable-volume", action="store_true", default=None, help="disable volume control")

    brightness_group = run_parser.add_mutually_exclusive_group()
    brightness_group.add_argument("--enable-brightness", action="store_true", default=None, help="enable brightness control")
    brightness_group.add_argument("--disable-brightness", action="store_true", default=None, help="disable brightness control")

    tap_group = run_parser.add_mutually_exclusive_group()
    tap_group.add_argument("--enable-tap", action="store_true", default=None, help="enable 4-finger tap action")
    tap_group.add_argument("--disable-tap", action="store_true", default=None, help="disable 4-finger tap action")

    run_parser.add_argument("--volume-axis", choices=["vertical", "horizontal"], help="gesture axis for volume control")
    run_parser.add_argument("--brightness-axis", choices=["vertical", "horizontal"], help="gesture axis for brightness control")
    run_parser.add_argument("--tap-action", choices=["super_key", "custom_command"], help="action to trigger on 4-finger tap")

    # 'check' subcommand
    check_parser = subparsers.add_parser("check", help="check system eligibility for fingerswipe")
    check_parser.add_argument("--library", type=Path, help="native shared library")

    # 'config' subcommand
    config_parser = subparsers.add_parser("config", help="view or modify configuration file")
    config_sub = config_parser.add_subparsers(dest="config_command")
    set_parser = config_sub.add_parser("set", help="set configuration values")
    set_parser.add_argument("--tap-action", choices=["super_key", "custom_command"], help="4-finger tap action mode")
    set_parser.add_argument("--tap-cmd", help="custom shell command for 4-finger tap")
    set_parser.add_argument("--volume-axis", choices=["vertical", "horizontal"], help="volume control axis")
    set_parser.add_argument("--brightness-axis", choices=["vertical", "horizontal"], help="brightness control axis")
    config_sub.add_parser("reset", help="reset configuration to factory defaults")

    # 'gui' subcommand
    subparsers.add_parser("gui", help="launch visual GUI configurator in browser")

    args = parser.parse_args()

    if args.command == "check":
        results = run_eligibility_checks(args.library)
        passed = print_eligibility_report(results)
        sys.exit(0 if passed else 1)

    elif args.command == "config":
        if args.config_command == "reset":
            from fingerswipe.config import default_config_path
            cfg_path = default_config_path()
            if cfg_path.exists():
                cfg_path.unlink()
            print(f"✓ Configuration reset to factory defaults ({cfg_path})")
            sys.exit(0)
        elif args.config_command == "set":
            from fingerswipe.config import default_config_path
            cfg_path = default_config_path()
            cfg_path.parent.mkdir(parents=True, exist_ok=True)
            
            yaml = YAML()
            data: dict[str, Any] = {}
            if cfg_path.exists():
                try:
                    data = yaml.load(cfg_path) or {}
                except Exception:
                    data = {}

            if not isinstance(data, dict):
                data = {}

            tap_section = data.setdefault("tap", {})
            vol_section = data.setdefault("volume", {})
            bright_section = data.setdefault("brightness", {})

            if args.tap_action:
                tap_section["action"] = args.tap_action
            if args.tap_cmd is not None:
                tap_section["custom_command"] = args.tap_cmd
            if args.volume_axis:
                vol_section["axis"] = args.volume_axis
            if args.brightness_axis:
                bright_section["axis"] = args.brightness_axis

            with open(cfg_path, "w") as f:
                yaml.dump(data, f)

            print(f"✓ Configuration saved to {cfg_path}")
            sys.exit(0)
        else:
            config_parser.print_help()
            sys.exit(0)

    elif args.command == "gui":
        from fingerswipe.gui import launch_native_gui
        try:
            launch_native_gui()
        except KeyboardInterrupt:
            print("\n👋 FingerSwipe GUI closed.")
            sys.exit(0)
        sys.exit(0)

    elif args.command == "run":
        try:
            base_config = load_config(args.config)

            # Apply CLI overrides
            vol_enabled = base_config.volume.enabled
            if args.enable_volume:
                vol_enabled = True
            elif args.disable_volume:
                vol_enabled = False

            bright_enabled = base_config.brightness.enabled
            if args.enable_brightness:
                bright_enabled = True
            elif args.disable_brightness:
                bright_enabled = False

            tap_enabled = base_config.tap.enabled
            if args.enable_tap:
                tap_enabled = True
            elif args.disable_tap:
                tap_enabled = False

            vol_axis = args.volume_axis or base_config.volume.axis
            bright_axis = args.brightness_axis or base_config.brightness.axis
            tap_action = args.tap_action or base_config.tap.action

            if vol_enabled and bright_enabled and vol_axis == bright_axis:
                raise ConfigurationError("volume and brightness cannot be assigned to the same gesture axis")

            volume_cfg = VolumeConfig(
                enabled=vol_enabled,
                axis=vol_axis,
                minimum=base_config.volume.minimum,
                maximum=base_config.volume.maximum,
                step=base_config.volume.step,
                threshold=base_config.volume.threshold,
            )
            brightness_cfg = BrightnessConfig(
                enabled=bright_enabled,
                axis=bright_axis,
                minimum=base_config.brightness.minimum,
                maximum=base_config.brightness.maximum,
                step=base_config.brightness.step,
                threshold=base_config.brightness.threshold,
            )
            tap_cfg = TapConfig(
                enabled=tap_enabled,
                max_distance=base_config.tap.max_distance,
                max_duration_ms=base_config.tap.max_duration_ms,
                action=tap_action,
                custom_command=base_config.tap.custom_command,
            )
            config = Config(
                engine=base_config.engine,
                volume=volume_cfg,
                brightness=brightness_cfg,
                tap=tap_cfg,
                logging=base_config.logging,
            )

            configure_logging(config.logging.level, config.logging.json)
            library = load_native(args.library)
            curve = {"linear": LinearCurve, "power": PowerCurve,
                     "exponential": ExponentialCurve}[config.engine.curve]()

            with LibinputProvider(library) as provider:
                audio_backend = PipeWireBackend(library) if config.volume.enabled else None
                brightness_backend = NativeBrightnessBackend(library) if config.brightness.enabled else None
                tap_detector = None

                try:
                    if audio_backend:
                        audio_backend.connect()
                    if brightness_backend:
                        brightness_backend.connect()

                    vol_controller = VolumeController(audio_backend, config.volume) if audio_backend else None
                    bright_controller = BrightnessController(brightness_backend, config.brightness) if brightness_backend else None
                    tap_controller = TapController(config.tap, library) if config.tap.enabled else None

                    if tap_controller and config.tap.enabled:
                        tap_detector = Raw4FingerTapDetector(
                            on_tap_callback=tap_controller.trigger,
                            max_duration_ms=config.tap.max_duration_ms,
                        )
                        tap_detector.start()

                    vert_controller = vol_controller if config.volume.axis == "vertical" else bright_controller
                    horiz_controller = vol_controller if config.volume.axis == "horizontal" else bright_controller

                    router = GestureAxisRouter(
                        vertical_controller=vert_controller,
                        horizontal_controller=horiz_controller,
                        axis_lock_threshold=config.engine.axis_lock_threshold,
                    )

                    def on_config_reload() -> None:
                        try:
                            new_cfg = load_config(args.config)
                            if tap_controller:
                                tap_controller.update_config(new_cfg.tap)
                            if vol_controller:
                                vol_controller.update_config(new_cfg.volume)
                            if bright_controller:
                                bright_controller.update_config(new_cfg.brightness)
                            router.update_axis_lock_threshold(new_cfg.engine.axis_lock_threshold)
                            if tap_detector:
                                tap_detector._max_duration_ms = new_cfg.tap.max_duration_ms
                            logging.getLogger("fingerswipe").info(
                                "Live configuration reloaded successfully: tap action='%s', cmd='%s'",
                                new_cfg.tap.action,
                                new_cfg.tap.custom_command,
                            )
                        except Exception as reload_err:
                            logging.getLogger("fingerswipe").error("Config reload failed: %s", reload_err)

                    app = Application(
                        provider,
                        GestureEngine(config.engine, curve),
                        router,
                        on_config_reload=on_config_reload,
                        config_path=args.config,
                    )
                    for signum in (signal.SIGINT, signal.SIGTERM):
                        signal.signal(signum, lambda _signum, _frame: app.stop())
                    app.run()
                finally:
                    if tap_detector:
                        tap_detector.stop()
                    if audio_backend:
                        audio_backend.disconnect()
                    if brightness_backend:
                        brightness_backend.disconnect()

        except (ConfigurationError, NativeError) as error:
            logging.getLogger("fingerswipe").critical("%s", error)
            raise SystemExit(1) from error
        except KeyboardInterrupt:
            raise SystemExit(0) from None

