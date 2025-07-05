from core.lock.lock import Lock

class DummyLock(Lock):
    def __init__(self):
        self.acquired = False
        self.released = False
    def acquire(self, blocking: bool = True, timeout: float = -1) -> bool:
        self.acquired = True
        return True
    def release(self) -> None:
        self.released = True

def test_lock_interface_context_manager():
    lock = DummyLock()
    with lock:
        assert lock.acquired
    assert lock.released
