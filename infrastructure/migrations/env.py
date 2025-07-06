
from alembic import context
from logging.config import fileConfig
from core.config.config import get_database_url  # Use your central config logic
from sqlalchemy import create_engine

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
fileConfig(config.config_file_name)


# Alembic requires a 'sqlalchemy.url' config variable for the database connection string.
# This is needed even if you are not using SQLAlchemy ORM features.
# The value should be a standard SQLAlchemy-style URL, e.g.:
# postgresql+psycopg2://user:password@host:port/dbname
config.set_main_option("sqlalchemy.url", get_database_url())


# --- Alembic migration runner logic ---
target_metadata = None  # No SQLAlchemy models; using raw SQL migrations

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    url = config.get_main_option("sqlalchemy.url")
    engine = create_engine(url)
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
