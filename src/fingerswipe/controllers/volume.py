from fingerswipe.backends.base import AudioBackend
from fingerswipe.config import VolumeConfig
from fingerswipe.controllers.base import Controller
from fingerswipe.engine.motion import ProcessedMotion
from fingerswipe.interactions.phase import GesturePhase


class VolumeController(Controller):

    def __init__(
        self,
        backend: AudioBackend,
        config: VolumeConfig,
    ) -> None:
        self._backend = backend
        self._minimum = config.minimum
        self._maximum = config.maximum
        self._step = config.step
        self._threshold = config.threshold
        self._current_volume: float | None = None
        self._buffer = 0.0

    def handle(self, motion: ProcessedMotion) -> None:
        if motion.phase is GesturePhase.BEGIN:
            self._current_volume = self._backend.get_volume()
            self._buffer = 0.0
            return

        if motion.phase in (GesturePhase.END, GesturePhase.CANCEL):
            self._current_volume = None
            self._buffer = 0.0
            return

        if motion.phase is not GesturePhase.UPDATE:
            return

        if self._current_volume is None:
            self._current_volume = self._backend.get_volume()
            self._buffer = 0.0

        self._buffer += motion.dy

        while self._buffer <= -self._threshold:
            self._current_volume = min(self._maximum, self._current_volume + self._step)
            self._backend.set_volume(self._current_volume)
            self._buffer += self._threshold

        while self._buffer >= self._threshold:
            self._current_volume = max(self._minimum, self._current_volume - self._step)
            self._backend.set_volume(self._current_volume)
            self._buffer -= self._threshold