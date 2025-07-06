from core.lock.in_process import InProcessLock


def test_lock_acquire_release():
    lock = InProcessLock("resource1")
    assert lock.acquire()
    lock.release()


def test_lock_context_manager():
    lock = InProcessLock("resource2")
    acquired = False
    with lock:
        acquired = True
        assert lock._lock.locked()
    assert acquired
    assert not lock._lock.locked()


def test_named_locks_are_shared():
    lock1 = InProcessLock("shared")
    lock2 = InProcessLock("shared")
    assert lock1._lock is lock2._lock
    assert lock1.name == lock2.name == "shared"


def test_different_named_locks_are_distinct():
    lock1 = InProcessLock("a")
    lock2 = InProcessLock("b")
    assert lock1._lock is not lock2._lock
    assert lock1.name == "a"
    assert lock2.name == "b"
