import os
from typing import NoReturn

def load_env(env_path: str = '.env') -> None:
    """
    Loads environment variables from a .env file into os.environ.
    """
    if not os.path.exists(env_path):
        raise FileNotFoundError(f".env file not found at {env_path}")
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line:
                continue
            key, value = line.split('=', 1)
            os.environ.setdefault(key.strip(), value.strip())
