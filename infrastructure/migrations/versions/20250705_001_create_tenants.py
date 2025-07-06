"""
Revision ID: 20250705_001_create_tenants
Revises = None
Create Date: 2025-07-05

This migration creates the tenants table.
"""

# Alembic revision identifiers, used by Alembic.
from alembic import op
revision = '20250705_001_create_tenants'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute('''
    CREATE TABLE IF NOT EXISTS tenants (
        id UUID PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    ''')

def downgrade():
    op.execute('''
    DROP TABLE IF EXISTS tenants;
    ''')
