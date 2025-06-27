from .load_env import load_env
import os

def get_alpha_vantage_api_key(env_path='.env'):
    """
    Loads the .env file and returns the Alpha Vantage API key.
    """
    load_env(env_path)
    api_key = os.environ.get('ALPHA_VANTAGE_API_KEY')
    if not api_key:
        raise ValueError("ALPHA_VANTAGE_API_KEY not found in environment variables.")
    return api_key
