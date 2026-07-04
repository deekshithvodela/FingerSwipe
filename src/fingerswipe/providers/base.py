from abc import ABC, abstractmethod
from collections.abc import Iterator

from fingerswipe.interactions.event import GestureEvent


class Provider(ABC):

    @abstractmethod
    def stop(self) -> None:
        """Request termination of event iteration."""
        raise NotImplementedError

    @abstractmethod
    def events(self) -> Iterator[GestureEvent]:
        """Yield gesture events indefinitely."""
        raise NotImplementedError
