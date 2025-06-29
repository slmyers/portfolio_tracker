from psycopg2.pool import SimpleConnectionPool
from core.config.config import get_postgres_config
import contextlib

class CursorWithDeadline:
    def __init__(self, cursor, deadline_manager=None):
        self._cursor = cursor
        self._deadline_manager = deadline_manager
    def execute(self, *args, **kwargs):
        if self._deadline_manager:
            self._deadline_manager.check()
        return self._cursor.execute(*args, **kwargs)
    def __getattr__(self, name):
        return getattr(self._cursor, name)
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self._cursor.__exit__(exc_type, exc_val, exc_tb)


class PostgresPool:
    def __init__(self, config=None, connection_pool_cls=SimpleConnectionPool):
        cfg = config or get_postgres_config()
        self.pool = connection_pool_cls(
            minconn=1,
            maxconn=10,
            user=cfg.user,
            password=cfg.password,
            host=cfg.host,
            port=cfg.port,
            database=cfg.db,
        )

    @contextlib.contextmanager
    def connection(self, deadline_manager=None):
        conn = self.pool.getconn()
        try:
            yield conn, deadline_manager
        finally:
            self.pool.putconn(conn)

    def get_conn(self):
        return self.pool.getconn()

    def put_conn(self, conn):
        self.pool.putconn(conn)

    def closeall(self):
        self.pool.closeall()
