from abc import ABC, abstractmethod


class Curve(ABC):

    @abstractmethod
    def transform(self, value: float) -> float:
        """Transform a normalized value."""
        raise NotImplementedError