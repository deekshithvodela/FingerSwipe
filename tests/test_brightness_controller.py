import pytest
from fingerswipe.config import BrightnessConfig
from fingerswipe.controllers.brightness import BrightnessController
from fingerswipe.engine.motion import ProcessedMotion
from fingerswipe.interactions.phase import GesturePhase


class FakeBrightnessBackend:
    def __init__(self, value: float) -> None:
        self.value = value

    def connect(self) -> None: pass
    def disconnect(self) -> None: pass
    def get_brightness(self) -> float: return self.value
    def set_brightness(self, value: float) -> None: self.value = value


def test_horizontal_update_changes_and_clamps_brightness() -> None:
    backend = FakeBrightnessBackend(0.5)
    controller = BrightnessController(backend, BrightnessConfig(minimum=0.1, maximum=0.9, step=0.1, threshold=0.2))  # type: ignore[arg-type]

    # Starting at 0.5, dx = 0.5 (right, brightness increases by 2 * 0.1 = 0.2)
    controller.handle(ProcessedMotion(GesturePhase.UPDATE, 0.5, 0.0))
    assert backend.value == pytest.approx(0.7)

    # Brightness is 0.7, buffer is 0.1. dx = -0.5 (left, brightness decreases by 2 * 0.1 = 0.2)
    controller.handle(ProcessedMotion(GesturePhase.UPDATE, -0.5, 0.0))
    assert backend.value == pytest.approx(0.5)

    # Brightness is 0.5, buffer is 0.0. dx = 1.0 (right, brightness increases to 1.0, clamped to 0.9)
    controller.handle(ProcessedMotion(GesturePhase.UPDATE, 1.0, 0.0))
    assert backend.value == pytest.approx(0.9)


def test_brightness_caching_lifecycle() -> None:
    backend = FakeBrightnessBackend(0.5)
    controller = BrightnessController(backend, BrightnessConfig(step=0.02, threshold=0.05))  # type: ignore[arg-type]

    # 1. BEGIN gesture cache initialization
    controller.handle(ProcessedMotion(GesturePhase.BEGIN, 0.0, 0.0))
    assert controller._current_brightness == pytest.approx(0.5)

    # 2. UPDATE updates cached brightness and backend
    controller.handle(ProcessedMotion(GesturePhase.UPDATE, 0.1, 0.0))
    assert controller._current_brightness == pytest.approx(0.54)
    assert backend.value == pytest.approx(0.54)

    # 3. END gesture clears the session
    controller.handle(ProcessedMotion(GesturePhase.END, 0.0, 0.0))
    assert controller._current_brightness is None
