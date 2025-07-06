import time
import pytest
from core.deadline_manager import DeadlineManager, DeadlineExceeded

def test_deadline_manager_not_exceeded():
    deadline = DeadlineManager(timeout_seconds=1)
    # Should not raise
    deadline.check()

def test_deadline_manager_exceeded():
    deadline = DeadlineManager(timeout_seconds=0)
    time.sleep(0.01)
    with pytest.raises(DeadlineExceeded):
        deadline.check()

def test_deadline_manager_multiple_checks():
    deadline = DeadlineManager(timeout_seconds=0.05)
    for _ in range(3):
        deadline.check()
        time.sleep(0.01)
    time.sleep(0.05)
    with pytest.raises(DeadlineExceeded):
        deadline.check()
