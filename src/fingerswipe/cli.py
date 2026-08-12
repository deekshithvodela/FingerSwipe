from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from fingerswipe.app import Application
from fingerswipe.version import __version__
from fingerswipe.backends.brightness import NativeBrightnessBackend
from fingerswipe.backends.pipewire import PipeWireBackend
from fingerswipe.config import BrightnessConfig, Config, ConfigurationError, VolumeConfig, load_config
from fingerswipe.controllers.brightness import BrightnessController
from fingerswipe.controllers.router import GestureAxisRouter
from fingerswipe.controllers.volume import VolumeController
from fingerswipe.curves.exponential import ExponentialCurve
from fingerswipe.curves.linear import LinearCurve
from fingerswipe.curves.power import PowerCurve
from fingerswipe.engine.processor import GestureEngine
from fingerswipe.logger import configure_logging
from fingerswipe.native import NativeError, load_native
from fingerswipe.providers.libinput import LibinputProvider
from fingerswipe.eligibility import run_eligibility_checks, print_eligibility_report


def main() -> None:
    # Handle backward compatibility: default to "run" if no subcommand is provided
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] not in ("check", "run", "-h", "--help", "-v", "--version")):
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

    run_parser.add_argument("--volume-axis", choices=["vertical", "horizontal"], help="gesture axis for volume control")
    run_parser.add_argument("--brightness-axis", choices=["vertical", "horizontal"], help="gesture axis for brightness control")

    # 'check' subcommand
    check_parser = subparsers.add_parser("check", help="check system eligibility for fingerswipe")
    check_parser.add_argument("--library", type=Path, help="native shared library")

    args = parser.parse_args()

    if args.command == "check":
        results = run_eligibility_checks(args.library)
        passed = print_eligibility_report(results)
        sys.exit(0 if passed else 1)

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

            vol_axis = args.volume_axis or base_config.volume.axis
            bright_axis = args.brightness_axis or base_config.brightness.axis

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
            config = Config(
                engine=base_config.engine,
                volume=volume_cfg,
                brightness=brightness_cfg,
                logging=base_config.logging,
            )

            configure_logging(config.logging.level, config.logging.json)
            library = load_native(args.library)
            curve = {"linear": LinearCurve, "power": PowerCurve,
                     "exponential": ExponentialCurve}[config.engine.curve]()

            with LibinputProvider(library) as provider:
                audio_backend = PipeWireBackend(library) if config.volume.enabled else None
                brightness_backend = NativeBrightnessBackend(library) if config.brightness.enabled else None

                try:
                    if audio_backend:
                        audio_backend.connect()
                    if brightness_backend:
                        brightness_backend.connect()

                    vol_controller = VolumeController(audio_backend, config.volume) if audio_backend else None
                    bright_controller = BrightnessController(brightness_backend, config.brightness) if brightness_backend else None

                    vert_controller = vol_controller if config.volume.axis == "vertical" else bright_controller
                    horiz_controller = vol_controller if config.volume.axis == "horizontal" else bright_controller

                    router = GestureAxisRouter(
                        vertical_controller=vert_controller,
                        horizontal_controller=horiz_controller,
                        axis_lock_threshold=config.engine.axis_lock_threshold,
                    )
                    app = Application(provider, GestureEngine(config.engine, curve), router)
                    for signum in (signal.SIGINT, signal.SIGTERM):
                        signal.signal(signum, lambda _signum, _frame: app.stop())
                    app.run()
                finally:
                    if audio_backend:
                        audio_backend.disconnect()
                    if brightness_backend:
                        brightness_backend.disconnect()

        except (ConfigurationError, NativeError) as error:
            logging.getLogger("fingerswipe").critical("%s", error)
            raise SystemExit(1) from error
        except KeyboardInterrupt:
            raise SystemExit(0) from None

