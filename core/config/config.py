from .load_env import load_env
import os
from typing import Optional

def get_alpha_vantage_api_key(env_path: str = '.env') -> str:
    """
    Loads the .env file and returns the Alpha Vantage API key.
    """
    load_env(env_path)
    api_key: Optional[str] = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        raise ValueError("ALPHA VANTAGE API key not found in environment variables.")
    return api_key
