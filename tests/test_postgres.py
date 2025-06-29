import pytest
from core.persistence.postgres import PostgresPool, CursorWithDeadline
from core.persistence.deadline_manager import DeadlineManager, DeadlineExceeded

class DummyConn:
    def cursor(self):
        return DummyCursor()
    def close(self):
        pass

class DummyCursor:
    def __init__(self):
        self.executed = False
    def execute(self, *args, **kwargs):
        self.executed = True
        return 'executed'
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def test_postgres_pool_uses_injected_pool():
    class DummyPool:
        def __init__(self, **kwargs):
            self.conn = DummyConn()
        def getconn(self):
            return self.conn
        def putconn(self, conn):
            self.conn = conn
        def closeall(self):
            pass
    pool = PostgresPool(connection_pool_cls=DummyPool)
    conn = pool.get_conn()
    assert isinstance(conn, DummyConn)
    pool.put_conn(conn)
    pool.closeall()

def test_cursor_with_deadline_executes():
    cur = DummyCursor()
    deadline = DeadlineManager(timeout_seconds=1)
    with CursorWithDeadline(cur, deadline) as c:
        result = c.execute('SELECT 1')
        assert cur.executed
        assert result == 'executed'

def test_cursor_with_deadline_raises_on_expired():
    cur = DummyCursor()
    deadline = DeadlineManager(timeout_seconds=0)
    # Simulate deadline exceeded
    import time
    time.sleep(0.01)
    with CursorWithDeadline(cur, deadline) as c:
        with pytest.raises(DeadlineExceeded):
            c.execute('SELECT 1')

def test_deadline_manager_check():
    deadline = DeadlineManager(timeout_seconds=0)
    import time
    time.sleep(0.01)
    with pytest.raises(DeadlineExceeded):
        deadline.check()
