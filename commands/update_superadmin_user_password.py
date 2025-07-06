"""
Command to update the SUPER_ADMIN user's password from the command line.
"""
import sys
from uuid import UUID
from getpass import getpass
from domain.user.repository.postgres import PostgresUserRepository
from domain.user.user_service import UserService
from core.di_container import Container

SUPER_ADMIN_USER_ID = UUID('00000000-0000-0000-0000-000000000002')

def main():
    if len(sys.argv) > 1:
        new_password = sys.argv[1]
    else:
        new_password = getpass("Enter new SUPER_ADMIN user password: ")
    container = Container()
    pool = container.postgres_pool()
    conn = pool.get_conn()
    try:
        repo = PostgresUserRepository(conn)
        service = UserService(repo)
        service.change_user_password(SUPER_ADMIN_USER_ID, new_password, conn=conn)
        conn.commit()
        print("SUPER_ADMIN user password updated successfully.")
    except Exception as e:
        conn.rollback()
        print(f"Error updating SUPER_ADMIN user password: {e}")
    finally:
        pool.put_conn(conn)

if __name__ == "__main__":
    main()
