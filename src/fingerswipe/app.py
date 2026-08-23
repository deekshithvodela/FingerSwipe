from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Callable

from fingerswipe.config import default_config_path
from fingerswipe.controllers.base import Controller
from fingerswipe.engine.base import Engine
from fingerswipe.providers.base import Provider


class Application:

    def __init__(
        self,
        provider: Provider,
        engine: Engine,
        controller: Controller,
        on_config_reload: Callable[[], None] | None = None,
        config_path: Path | None = None,
    ) -> None:
        self._provider, self._engine, self._controller = provider, engine, controller
        self._on_config_reload = on_config_reload
        self._config_path = config_path or default_config_path()
        self._last_mtime: float = self._get_mtime()
        self._running = False
        self._watcher_thread: threading.Thread | None = None

    def _get_mtime(self) -> float:
        try:
            return self._config_path.stat().st_mtime if self._config_path.exists() else 0.0
        except Exception:
            return 0.0

    def _start_config_watcher(self) -> None:
        def watcher_loop() -> None:
            while self._running:
                time.sleep(0.5)
                if self._on_config_reload:
                    current_mtime = self._get_mtime()
                    if current_mtime != self._last_mtime:
                        self._last_mtime = current_mtime
                        logging.getLogger(__name__).info("Detected config.yaml change — auto-reloading settings")
                        try:
                            self._on_config_reload()
                        except Exception as err:
                            logging.getLogger(__name__).error("Failed to reload config: %s", err)

        self._watcher_thread = threading.Thread(target=watcher_loop, daemon=True)
        self._watcher_thread.start()

    def run(self) -> None:
        logging.getLogger(__name__).info("FingerSwipe started")
        self._running = True
        if self._on_config_reload:
            self._start_config_watcher()

        try:
            for event in self._provider.events():
                self._controller.handle(self._engine.process(event))
        finally:
            self.stop()

    def stop(self) -> None:
        self._running = False
        self._provider.stop()
