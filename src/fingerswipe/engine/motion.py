from dataclasses import dataclass

from fingerswipe.interactions.phase import GesturePhase


@dataclass(slots=True, frozen=True)
class ProcessedMotion:
    phase: GesturePhase
    dx: float
    dy: float