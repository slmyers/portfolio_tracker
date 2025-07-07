

# Database Migration Design (Alembic with Embedded SQL)

## Purpose
This document describes how to manage database schema changes using Alembic as a migration harness, writing all migrations as Python scripts that execute raw SQL using `op.execute`. This approach provides full control, transparency, and robust version tracking, and supports both schema and data migrations.

## Tooling
- **Alembic**: Used as a migration runner and version tracker. No autogeneration or ORM features are used.
- **Embedded SQL**: All schema and data changes are written as Python migration scripts using `op.execute` with SQL strings for clarity and auditability.

## Setup
1. Install Alembic:
   ```sh
   pip install alembic
   ```
2. Initialize Alembic in your project (if not already done):
   ```sh
   alembic init infrastructure/migrations
   ```
3. Configure your database connection in `alembic.ini` (or via environment variables in `env.py`).
4. All migration scripts are Python files in `infrastructure/migrations/versions/`.

## Writing and Applying Migrations
1. **Create a new migration:**
   - Generate a migration file using Alembic:
     ```sh
     alembic -c infrastructure/migrations/alembic.ini revision -m "describe your migration"
     ```
   - Edit the generated Python file in `infrastructure/migrations/versions/` and write your schema or data changes using `op.execute` with SQL strings.
   - Example (schema migration):
     ```python
     from alembic import op
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
         op.execute('DROP TABLE IF EXISTS tenants;')
     ```
   - Example (data migration):
     ```python
     from alembic import op
     def upgrade():
         op.execute("""
         INSERT INTO tenants (id, name, is_active)
         VALUES ('00000000-0000-0000-0000-000000000001', 'system', TRUE)
         ON CONFLICT (id) DO NOTHING;
         """)
     def downgrade():
         op.execute("""
         DELETE FROM tenants WHERE id = '00000000-0000-0000-0000-000000000001';
         """)
     ```
2. **Apply migrations:**
   ```sh
   PYTHONPATH=$(pwd) (TEST_ENV=true)? alembic -c infrastructure/migrations/alembic.ini upgrade head
   ```
   Alembic will track which migrations have been applied in the database.

## Folder Structure
- `infrastructure/migrations/` — Alembic config and migration scripts
  - `alembic.ini` — Alembic configuration file
  - `env.py` — Alembic environment file (can be customized to load DB URL from .env)
  - `versions/` — Contains Alembic migration scripts (`.py`)

## Best Practices
- Write clear, idempotent SQL for all migrations, embedded in Python scripts.
- Keep migration scripts in version control.
- Test migrations on a copy of production data before rollout.
- Never edit applied migration scripts; create new ones for changes.
- Document each migration's purpose and impact in the script header.
- Use Alembic only for version tracking and running SQL, not for autogeneration.

## Example Alembic Migration Script
```python
"""
Revision ID: 20250705_001_create_tenants
Revises = None
Create Date: 2025-07-05

This migration creates the tenants table.
"""
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
    op.execute('DROP TABLE IF EXISTS tenants;')
```



## References
- [Alembic Documentation](https://alembic.sqlalchemy.org/en/latest/)
