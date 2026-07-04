import pytest

from fingerswipe.config import EngineConfig
from fingerswipe.curves.linear import LinearCurve
from fingerswipe.engine.processor import GestureEngine
from fingerswipe.interactions.event import GestureEvent
from fingerswipe.interactions.phase import GesturePhase


def event(phase: GesturePhase, dy: float) -> GestureEvent:
    return GestureEvent(phase, 0.0, dy, 1.0)


def test_engine_filters_scales_and_smooths_motion() -> None:
    engine = GestureEngine(EngineConfig(0.1, 0.5, 2.0, "linear"), LinearCurve())
    engine.process(event(GesturePhase.BEGIN, 0.0))
    assert engine.process(event(GesturePhase.UPDATE, 0.05)).dy == 0.0
    assert engine.process(event(GesturePhase.UPDATE, 0.4)).dy == pytest.approx(0.4)


def test_end_resets_filter_state() -> None:
    engine = GestureEngine(EngineConfig(0.0, 0.5, 1.0, "linear"), LinearCurve())
    engine.process(event(GesturePhase.UPDATE, 1.0))
    engine.process(event(GesturePhase.END, 1.0))
    assert engine.process(event(GesturePhase.BEGIN, 0.0)).dy == 0.0
