from abc import ABC, abstractmethod

from fingerswipe.engine.motion import ProcessedMotion
from fingerswipe.interactions.event import GestureEvent


class Engine(ABC):

    @abstractmethod
    def process(self, event: GestureEvent) -> ProcessedMotion:
        """Convert raw gesture events into processed motion."""
        raise NotImplementedError