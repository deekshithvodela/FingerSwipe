import pytest
from fingerswipe.config import VolumeConfig
from fingerswipe.controllers.volume import VolumeController
from fingerswipe.engine.motion import ProcessedMotion
from fingerswipe.interactions.phase import GesturePhase


class FakeAudio:
    def __init__(self, volume: float) -> None:
        self.volume = volume
    def connect(self) -> None: pass
    def disconnect(self) -> None: pass
    def get_volume(self) -> float: return self.volume
    def set_volume(self, volume: float) -> None: self.volume = volume
    def is_muted(self) -> bool: return False
    def set_muted(self, muted: bool) -> None: pass


def test_vertical_update_changes_and_clamps_volume() -> None:
    audio = FakeAudio(0.5)
    controller = VolumeController(audio, VolumeConfig(minimum=0.2, maximum=0.8, step=0.1, threshold=0.2))  # type: ignore[arg-type]
    
    # Starting at 0.5, dy = -0.5 (up, volume increases by 2 * 0.1 = 0.2)
    controller.handle(ProcessedMotion(GesturePhase.UPDATE, 0.0, -0.5))
    assert audio.volume == pytest.approx(0.7)
    
    # Volume is 0.7, buffer is -0.1. dy = 0.5 (down, volume decreases by 2 * 0.1 = 0.2)
    controller.handle(ProcessedMotion(GesturePhase.UPDATE, 0.0, 0.5))
    assert audio.volume == pytest.approx(0.5)
    
    # Volume is 0.5, buffer is 0.0. dy = -1.0 (up, volume increases to 1.0, clamped to 0.8)
    controller.handle(ProcessedMotion(GesturePhase.UPDATE, 0.0, -1.0))
    assert audio.volume == pytest.approx(0.8)


def test_non_update_is_ignored() -> None:
    audio = FakeAudio(0.5)
    VolumeController(audio, VolumeConfig()).handle(  # type: ignore[arg-type]
        ProcessedMotion(GesturePhase.END, 0.0, 1.0))
    assert audio.volume == pytest.approx(0.5)


def test_volume_caching_lifecycle() -> None:
    audio = FakeAudio(0.5)
    controller = VolumeController(audio, VolumeConfig(step=0.02, threshold=0.05))  # type: ignore[arg-type]
    
    # 1. BEGIN gesture cache initialization
    controller.handle(ProcessedMotion(GesturePhase.BEGIN, 0.0, 0.0))
    assert controller._current_volume == pytest.approx(0.5)
    
    # 2. UPDATE updates the cached volume and backend
    controller.handle(ProcessedMotion(GesturePhase.UPDATE, 0.0, 0.1))
    assert controller._current_volume == pytest.approx(0.46)
    assert audio.volume == pytest.approx(0.46)
    
    # 3. External change during gesture is ignored in the active cache session
    audio.volume = 0.8
    controller.handle(ProcessedMotion(GesturePhase.UPDATE, 0.0, 0.1))
    assert controller._current_volume == pytest.approx(0.42)
    assert audio.volume == pytest.approx(0.42)
    
    # 4. END gesture clears the cache session
    controller.handle(ProcessedMotion(GesturePhase.END, 0.0, 0.0))
    assert controller._current_volume is None
    
    # 5. Next gesture BEGIN refreshes cache with external changes
    audio.volume = 0.8
    controller.handle(ProcessedMotion(GesturePhase.BEGIN, 0.0, 0.0))
    assert controller._current_volume == pytest.approx(0.8)
