from fingerswipe.config import EngineConfig
from fingerswipe.curves.base import Curve
from fingerswipe.engine.base import Engine
from fingerswipe.engine.motion import ProcessedMotion
from fingerswipe.interactions.event import GestureEvent
from fingerswipe.interactions.phase import GesturePhase


class GestureEngine(Engine):

    def __init__(
        self,
        config: EngineConfig,
        curve: Curve,
    ) -> None:
        self._config = config
        self._curve = curve

        self._last_dx = 0.0
        self._last_dy = 0.0

    def process(self, event: GestureEvent) -> ProcessedMotion:
        if event.phase is GesturePhase.BEGIN:
            self._last_dx = 0.0
            self._last_dy = 0.0

        dx = self._process_axis(event.dx, self._last_dx)
        dy = self._process_axis(event.dy, self._last_dy)

        self._last_dx = dx
        self._last_dy = dy

        if event.phase in (GesturePhase.END, GesturePhase.CANCEL):
            self._last_dx = 0.0
            self._last_dy = 0.0

        return ProcessedMotion(
            phase=event.phase,
            dx=dx,
            dy=dy,
        )

    def _process_axis(self, value: float, previous: float) -> float:
        if abs(value) < self._config.dead_zone:
            value = 0.0

        value *= self._config.sensitivity

        alpha = self._config.smoothing
        value = previous + alpha * (value - previous)

        if self._config.curve != "linear":
            value = max(-1.0, min(1.0, value))

        value = self._curve.transform(value)

        return value