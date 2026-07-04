from abc import ABC, abstractmethod

from fingerswipe.engine.motion import ProcessedMotion


class Controller(ABC):

    @abstractmethod
    def handle(self, motion: ProcessedMotion) -> None:
        """Handle processed gesture motion."""
        raise NotImplementedError