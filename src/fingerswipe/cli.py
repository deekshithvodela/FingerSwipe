from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

from fingerswipe.app import Application
from fingerswipe.backends.pipewire import PipeWireBackend
from fingerswipe.config import ConfigurationError, load_config
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
    if len(sys.argv) == 1 or (len(sys.argv) > 1 and sys.argv[1] not in ("check", "run", "-h", "--help")):
        sys.argv.insert(1, "run")

    parser = argparse.ArgumentParser(description="Control PipeWire volume with a three-finger swipe")
    subparsers = parser.add_subparsers(dest="command", help="subcommands")

    # 'run' subcommand
    run_parser = subparsers.add_parser("run", help="run the volume controller service")
    run_parser.add_argument("--config", type=Path, help="configuration file")
    run_parser.add_argument("--library", type=Path, help="native shared library")

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
            config = load_config(args.config)
            configure_logging(config.logging.level, config.logging.json)
            library = load_native(args.library)
            curve = {"linear": LinearCurve, "power": PowerCurve,
                     "exponential": ExponentialCurve}[config.engine.curve]()
            with LibinputProvider(library) as provider:
                with PipeWireBackend(library) as backend:
                    app = Application(provider, GestureEngine(config.engine, curve),
                                      VolumeController(backend, config.volume))
                    for signum in (signal.SIGINT, signal.SIGTERM):
                        signal.signal(signum, lambda _signum, _frame: app.stop())
                    app.run()
        except (ConfigurationError, NativeError) as error:
            logging.getLogger("fingerswipe").critical("%s", error)
            raise SystemExit(1) from error
        except KeyboardInterrupt:
            raise SystemExit(0) from None

