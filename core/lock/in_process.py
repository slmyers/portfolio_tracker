
from .lock import Lock
import threading
from typing import Dict, cast


class InProcessLock(Lock):
    """
    Named in-process lock using a shared registry of threading.Lock objects.
    """
    _registry: Dict[str, threading.Lock] = {}
    _registry_lock = threading.Lock()

    def __init__(self, name: str) -> None:
        self.name = name
        cls = self.__class__
        with cls._registry_lock:
            if name not in cls._registry:
                cls._registry[name] = threading.Lock()
            self._lock = cls._registry[name]

    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        if timeout == -1:
            return self._lock.acquire(blocking)
        return self._lock.acquire(blocking, timeout)

    def release(self) -> None:
        self._lock.release()
