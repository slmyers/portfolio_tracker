
"""
Revision ID: 20250705_002_create_users
Revises = '20250705_001_create_tenants'
Create Date: 2025-07-05

This migration creates the user_role enum, users table, and indexes.
"""

# Alembic revision identifiers, used by Alembic.
from alembic import op
revision = '20250705_002_create_users'
down_revision = '20250705_001_create_tenants'
branch_labels = None
depends_on = None

def upgrade():
    op.execute('''
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'user_role') THEN
            CREATE TYPE user_role AS ENUM ('user', 'admin', 'system', 'auditor', 'super_admin');
        END IF;
    END$$;
    ''')
    op.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id UUID PRIMARY KEY,
        tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
        email VARCHAR(255) NOT NULL,
        name VARCHAR(255) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        role user_role NOT NULL,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (tenant_id, email)
    );
    ''')
    op.execute('''
    CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
    ''')
    op.execute('''
    CREATE INDEX IF NOT EXISTS idx_users_tenant_id ON users(tenant_id);
    ''')

def downgrade():
    op.execute('''
    DROP INDEX IF EXISTS idx_users_tenant_id;
    ''')
    op.execute('''
    DROP INDEX IF EXISTS idx_users_email;
    ''')
    op.execute('''
    DROP TABLE IF EXISTS users;
    ''')
    op.execute('''
    DROP TYPE IF EXISTS user_role;
    ''')
