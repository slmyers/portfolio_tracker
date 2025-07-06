"""insert_default_tenant

Revision ID: b93b52d2b3db
Revises: 20250705_002_create_users
Create Date: 2025-07-05 18:47:04.869708

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'b93b52d2b3db'
down_revision: Union[str, Sequence[str], None] = '20250705_002_create_users'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Insert default tenant 'system'."""
    # Use a fixed UUID for the system tenant for referential integrity
    system_tenant_id = '00000000-0000-0000-0000-000000000001'
    op.execute(f"""
        INSERT INTO tenants (id, name, is_active)
        VALUES ('{system_tenant_id}', 'system', TRUE)
        ON CONFLICT (id) DO NOTHING;
    """)


def downgrade() -> None:
    """Downgrade schema: Remove default tenant 'system'."""
    system_tenant_id = '00000000-0000-0000-0000-000000000001'
    op.execute(f"""
        DELETE FROM tenants WHERE id = '{system_tenant_id}';
    """)
