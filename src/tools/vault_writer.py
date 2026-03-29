"""
Vault writer functions for Cocktail Cabinet.

Writes output back to the Obsidian vault — formatted cocktail suggestions
and cocktail log entries. Each function corresponds to a Gemini tool
declaration in declarations.py, allowing the LLM to call them to persist
its output.
"""
from datetime import date
from pathlib import Path

from src.config import OBSIDIAN_VAULT_PATH


def _vault_path(filename: str) -> Path:
    """Return the full path to a vault file.

    Args:
        filename: The markdown filename (e.g. 'Cocktail Suggestions.md').

    Returns:
        A Path object pointing to the file in the vault.
    """
    return Path(OBSIDIAN_VAULT_PATH) / filename


def write_suggestion(content: str) -> str:
    """Write a formatted cocktail suggestion to Cocktail Suggestions.md.

    Overwrites the file on each run. The content should include the
    recipe, missing ingredients with accessibility tiers, and a rating
    prompt. The vault template shows the expected format.

    Args:
        content: Formatted markdown content to write to the file.

    Returns:
        A confirmation message indicating the file was written.
    """
    path = _vault_path("Cocktail Suggestions.md")
    path.write_text(content, encoding="utf-8")
    return f"Cocktail suggestions written to {path}"


def write_to_log(cocktail: str, rating: int, notes: str = "") -> str:
    """Append a rated cocktail entry to Cocktail Log.md.

    Adds a new dated entry under the ## Log section. If the file does
    not exist, raises FileNotFoundError.

    Args:
        cocktail: Name of the cocktail.
        rating: Star rating from 1 to 5.
        notes: Optional tasting notes.

    Returns:
        A confirmation message indicating the entry was appended.

    Raises:
        ValueError: If rating is not between 1 and 5.
        FileNotFoundError: If Cocktail Log.md does not exist in the vault.
    """
    if not 1 <= rating <= 5:
        raise ValueError(f"Rating must be between 1 and 5, got {rating}.")

    path = _vault_path("Cocktail Log.md")
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find 'Cocktail Log.md' in vault at {OBSIDIAN_VAULT_PATH}. "
            f"Copy the file from vault_templates/ into your vault."
        )

    stars = "⭐" * rating
    today = date.today().isoformat()
    entry = f"\n### {today}\n**Cocktail:** {cocktail}\n**Rating:** {stars}\n**Notes:** {notes}\n"

    path.write_text(path.read_text(encoding="utf-8") + entry, encoding="utf-8")
    return f"Logged '{cocktail}' ({stars}) in Cocktail Log."
