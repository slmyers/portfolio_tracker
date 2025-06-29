from core.di_container import Container

# Simple example: connect to Postgres and list schemas
def main():
    container = Container()
    pool = container.postgres_pool()
    conn = pool.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT schema_name FROM information_schema.schemata;")
            schemas = cur.fetchall()
            print("Schemas:")
            for row in schemas:
                print(" -", row[0])
    finally:
        pool.put_conn(conn)

if __name__ == "__main__":
    main()
