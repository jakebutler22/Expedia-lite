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


def get_openrouter_api_key() -> str | None:
    """Return the configured OpenRouter key for backend-only use."""
    value = os.getenv("OPENROUTER_API_KEY")
    if value is None:
        return None
    normalized_value = value.strip()
    return normalized_value or None


def get_openrouter_model() -> str | None:
    """Return the explicit course-provided OpenRouter model setting."""
    value = os.getenv("OPENROUTER_MODEL")
    if value is None:
        return None
    normalized_value = value.strip()
    return normalized_value or None


def openrouter_configuration_status() -> dict[str, str]:
    """Describe OpenRouter configuration without exposing either value."""
    return {
        "openrouter_api_key_status": (
            "key is configured"
            if get_openrouter_api_key() is not None
            else "key is not configured"
        ),
        "openrouter_model_status": (
            "model is configured"
            if get_openrouter_model() is not None
            else "model is not configured"
        ),
    }
