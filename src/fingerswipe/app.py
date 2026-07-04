from __future__ import annotations

import logging
from fingerswipe.controllers.base import Controller
from fingerswipe.engine.base import Engine
from fingerswipe.providers.base import Provider


class Application:
    def __init__(self, provider: Provider, engine: Engine, controller: Controller) -> None:
        self._provider, self._engine, self._controller = provider, engine, controller

    def run(self) -> None:
        logging.getLogger(__name__).info("FingerSwipe started")
        for event in self._provider.events():
            self._controller.handle(self._engine.process(event))

    def stop(self) -> None:
        self._provider.stop()
