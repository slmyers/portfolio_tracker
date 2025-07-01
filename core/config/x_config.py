import os

def get_x_api_key(env_path: str = '.env') -> str:
    """
    Loads the .env file and returns the X (Grok) API key.
    """
    from core.config.load_env import load_env
    load_env(env_path)
    api_key = os.environ.get('X_API_KEY')
    if not api_key:
        raise ValueError("X_API_KEY not found in environment variables.")
    return api_key
