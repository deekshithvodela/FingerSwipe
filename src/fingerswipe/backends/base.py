from abc import ABC, abstractmethod


class AudioBackend(ABC):

    @abstractmethod
    def connect(self) -> None:
        """Initialize the backend."""
        raise NotImplementedError

    @abstractmethod
    def disconnect(self) -> None:
        """Release all resources."""
        raise NotImplementedError

    @abstractmethod
    def get_volume(self) -> float:
        """Return normalized volume in the range [0.0, 1.0]."""
        raise NotImplementedError

    @abstractmethod
    def set_volume(self, volume: float) -> None:
        """Set normalized volume in the range [0.0, 1.0]."""
        raise NotImplementedError

    @abstractmethod
    def is_muted(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def set_muted(self, muted: bool) -> None:
        raise NotImplementedError