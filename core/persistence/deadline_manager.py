import time

class DeadlineExceeded(Exception):
    pass

class DeadlineManager:
    def __init__(self, timeout_seconds):
        self.start = time.monotonic()
        self.timeout = timeout_seconds
    def check(self):
        if time.monotonic() - self.start > self.timeout:
            raise DeadlineExceeded("Request deadline exceeded")
