from .load_env import load_env
import os
from typing import Optional
from dataclasses import dataclass

@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: int
    user: str
    password: str
    db: str


@dataclass(frozen=True)
class RedisConfig:
    host: str
    port: int

def get_postgres_config(env_path: str = '.env') -> PostgresConfig:
    """
    Loads the .env file and returns a PostgresConfig object.
    """
    load_env(env_path)
    return PostgresConfig(
        host=os.environ.get('POSTGRES_HOST', 'localhost'),
        port=int(os.environ.get('POSTGRES_PORT', 5432)),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        password=os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        db=os.environ.get('POSTGRES_DB', 'portfolio_db'),
    )

def get_test_postgres_config(env_path: str = '.env') -> PostgresConfig:
    """
    Loads the .env file and returns a PostgresConfig object for the test database (db name is test_portfolio).
    """
    load_env(env_path)
    return PostgresConfig(
        host=os.environ.get('POSTGRES_HOST', 'localhost'),
        port=int(os.environ.get('POSTGRES_PORT', 5432)),
        user=os.environ.get('POSTGRES_USER', 'postgres'),
        password=os.environ.get('POSTGRES_PASSWORD', 'postgres'),
        db='test_portfolio_db',
    )

def get_database_url(env_path: str = '.env') -> str:
    """
    Loads the .env file and returns the database URL.
    If TEST_ENV is set to 'true' (case-insensitive) in the environment, use the test database name.
    """
    load_env(env_path)
    postgres_config = get_postgres_config(env_path)
    use_test_db = os.environ.get('TEST_ENV', '').lower() == 'true'
    db_name = 'test_portfolio_db' if use_test_db else 'portfolio_db'
    return f"postgresql+psycopg2://{postgres_config.user}:{postgres_config.password}@{postgres_config.host}:{postgres_config.port}/{db_name}"



def get_redis_config(env_path: str = '.env') -> RedisConfig:
    """
    Loads the .env file and returns a RedisConfig object.
    """
    load_env(env_path)
    return RedisConfig(
        host=os.environ.get('REDIS_HOST', 'localhost'),
        port=int(os.environ.get('REDIS_PORT', 6379)),
    )


def get_alpha_vantage_api_key(env_path: str = '.env') -> str:
    """
    Loads the .env file and returns the Alpha Vantage API key.
    """
    load_env(env_path)
    api_key: Optional[str] = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        raise ValueError("ALPHA VANTAGE API key not found in environment variables.")
    return api_key

def get_log_level(env_path: str = '.env') -> str:
    """
    Loads the .env file and returns the log level (default INFO).
    """
    load_env(env_path)
    return os.environ.get('LOG_LEVEL', 'INFO').upper()


def get_openai_api_key(env_path: str = '.env') -> str:
    """
    Loads the .env file and returns the OpenAI API key.
    """
    load_env(env_path)
    api_key: Optional[str] = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OpenAI API key not found in environment variables.")
    return api_key
