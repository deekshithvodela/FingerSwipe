from fingerswipe.backends.base import BrightnessBackend
from fingerswipe.config import BrightnessConfig
from fingerswipe.controllers.base import Controller
from fingerswipe.engine.motion import ProcessedMotion
from fingerswipe.interactions.phase import GesturePhase


class BrightnessController(Controller):

    def __init__(
        self,
        backend: BrightnessBackend,
        config: BrightnessConfig,
    ) -> None:
        self._backend = backend
        self._minimum = config.minimum
        self._maximum = config.maximum
        self._step = config.step
        self._threshold = config.threshold
        self._current_brightness: float | None = None
        self._buffer = 0.0

    def handle(self, motion: ProcessedMotion) -> None:
        if motion.phase is GesturePhase.BEGIN:
            self._current_brightness = self._backend.get_brightness()
            self._buffer = 0.0
            return

        if motion.phase in (GesturePhase.END, GesturePhase.CANCEL):
            self._current_brightness = None
            self._buffer = 0.0
            return

        if motion.phase is not GesturePhase.UPDATE:
            return

        if self._current_brightness is None:
            self._current_brightness = self._backend.get_brightness()
            self._buffer = 0.0

        self._buffer += motion.dx

        while self._buffer >= self._threshold:
            self._current_brightness = min(self._maximum, self._current_brightness + self._step)
            self._backend.set_brightness(self._current_brightness)
            self._buffer -= self._threshold

        while self._buffer <= -self._threshold:
            self._current_brightness = max(self._minimum, self._current_brightness - self._step)
            self._backend.set_brightness(self._current_brightness)
            self._buffer += self._threshold
