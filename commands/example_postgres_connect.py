from core.di_container import Container
from core.deadline_manager import DeadlineManager, DeadlineExceeded
from core.persistence.postgres import CursorWithDeadline
import time

# Example: connect to Postgres, list schemas, and demonstrate deadline enforcement
def main():
    container = Container()
    pool = container.postgres_pool()
    deadline = DeadlineManager(timeout_seconds=2)
    conn = pool.get_conn()
    try:
        # Usage 1: Plain cursor (no deadline enforcement)
        print("--- Plain cursor usage (no deadline enforcement) ---")
        with conn.cursor() as cur:
            cur.execute("SELECT schema_name FROM information_schema.schemata;")
            schemas = cur.fetchall()
            print("Schemas:")
            for row in schemas:
                print(" -", row[0])

        # Usage 2: CursorWithDeadline (enforces deadline)
        print("\n--- CursorWithDeadline usage (with deadline enforcement) ---")
        with conn.cursor() as cur:
            with CursorWithDeadline(cur, deadline) as cur_with_deadline:
                cur_with_deadline.execute("SELECT schema_name FROM information_schema.schemata;")
                schemas = cur_with_deadline.fetchall()
                print("Schemas:")
                for row in schemas:
                    print(" -", row[0])
                print("Testing deadline enforcement...")
                time.sleep(2.1)
                try:
                    cur_with_deadline.execute("SELECT 1;")
                except DeadlineExceeded as e:
                    print("Deadline exceeded:", e)
    finally:
        pool.put_conn(conn)

if __name__ == "__main__":
    main()
