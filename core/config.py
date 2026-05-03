import os
import yaml
from dotenv import load_dotenv
from loguru import logger

# Load the .env file
load_dotenv()

def load_config(path: str = "config.yaml") -> dict:
    """Reads config.yaml and returns it as a dictionary."""
    try:
        with open(path, "r") as f:
            config = yaml.safe_load(f)
            logger.info(f"Config loaded successfully from {path}")
            return config
    except FileNotFoundError:
        logger.error(f"config.yaml not found at {path}")
        return {}

def get_env(key: str, fallback: str = None) -> str:
    """Safely reads a value from the .env file."""
    value = os.getenv(key, fallback)
    if value is None:
        logger.warning(f"Environment variable '{key}' not found")
    return value