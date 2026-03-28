"""
Configuration loader for Cocktail Cabinet.

Reads required environment variables from a .env file at startup and
exposes them as typed constants. Raises a clear error if any required
variable is missing.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    """Return the value of a required environment variable.

    Args:
        key: The environment variable name.

    Raises:
        EnvironmentError: If the variable is missing or empty.
    """
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Missing required environment variable: {key}. "
            f"Copy .env.example to .env and fill in the values."
        )
    return value


GEMINI_API_KEY: str = _require("GEMINI_API_KEY")
OBSIDIAN_VAULT_PATH: str = _require("OBSIDIAN_VAULT_PATH")
