#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from fingerswipe.installer import install_system_integration


def main() -> None:
    parser = argparse.ArgumentParser(description="Install FingerSwipe system integration")
    parser.add_argument("--prefix", type=Path, default=Path("/usr"))
    args = parser.parse_args()
    install_system_integration(Path(__file__).resolve().parents[1], args.prefix)


if __name__ == "__main__":
    main()
