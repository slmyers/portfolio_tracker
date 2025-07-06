"""insert_default_user

Revision ID: 36a94e5c1c86
Revises: b93b52d2b3db
Create Date: 2025-07-05 18:48:17.555411

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = '36a94e5c1c86'
down_revision: Union[str, Sequence[str], None] = 'b93b52d2b3db'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Insert default SUPER ADMIN user for super_admin tenant."""
    # Use fixed UUIDs for referential integrity
    super_admin_tenant_id = '00000000-0000-0000-0000-000000000001'
    super_admin_user_id = '00000000-0000-0000-0000-000000000002'
    # Use a strong random hash for the password (change as needed)
    password_hash = '$2b$12$super_admin_placeholder_hash'  # bcrypt hash placeholder
    op.execute(f"""
        INSERT INTO users (id, tenant_id, email, name, password_hash, role, is_active)
        VALUES ('{super_admin_user_id}', '{super_admin_tenant_id}', 'super_admin@localhost', 'SUPER_ADMIN', '{password_hash}', 'super_admin', TRUE)
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    """Downgrade schema: Remove default SUPER ADMIN user."""
    super_admin_user_id = '00000000-0000-0000-0000-000000000002'
    op.execute(f"""
        DELETE FROM users WHERE id = '{super_admin_user_id}';
    """)
