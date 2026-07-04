from __future__ import annotations

import shutil
from pathlib import Path


def install_system_integration(source: Path, prefix: Path) -> None:
    destinations = {
        source / "install/99-fingerswipe.rules": prefix / "lib/udev/rules.d/99-fingerswipe.rules",
        source / "install/fingerswipe.service": prefix / "lib/systemd/user/fingerswipe.service",
        source / "config.yaml": prefix / "share/doc/fingerswipe/config.yaml",
    }
    for origin, destination in destinations.items():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(origin, destination)
