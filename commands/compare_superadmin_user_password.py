"""
Command to compare the SUPER_ADMIN user's password to a string input.
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
        password = sys.argv[1]
    else:
        password = getpass("Enter password to check against SUPER_ADMIN user: ")
    container = Container()
    pool = container.postgres_pool()
    conn = pool.get_conn()
    try:
        repo = PostgresUserRepository(conn)
        service = UserService(repo)
        ok, reason = service.verify_user_password(SUPER_ADMIN_USER_ID, password, conn=conn)
        if ok:
            print("Password matches SUPER_ADMIN user.")
        else:
            print(f"Password does NOT match SUPER_ADMIN user. Reason: {reason}")
    except Exception as e:
        print(f"Error comparing SUPER_ADMIN user password: {e}")
    finally:
        pool.put_conn(conn)

if __name__ == "__main__":
    main()
