from abc import ABC, abstractmethod

class Lock(ABC):
    """
    Generic lock interface for all lock backends.
    """

    @abstractmethod
    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        ...

    @abstractmethod
    def release(self) -> None:
        ...

    def __enter__(self) -> "Lock":
        self.acquire()
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        self.release()
