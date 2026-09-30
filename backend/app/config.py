import os
from pathlib import Path

from dotenv import load_dotenv


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = BACKEND_ROOT / ".env"

load_dotenv(dotenv_path=ENV_PATH)


def get_geoapify_api_key() -> str | None:
    """Return the configured Geoapify key for backend-only use."""
    value = os.getenv("GEOAPIFY_API_KEY")
    if value is None:
        return None
    normalized_value = value.strip()
    return normalized_value or None


def geoapify_api_key_status() -> str:
    """Describe whether the Geoapify key is configured without exposing it."""
    if get_geoapify_api_key() is None:
        return "key is not configured"
    return "key is configured"
