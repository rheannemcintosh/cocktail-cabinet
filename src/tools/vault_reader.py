"""
Vault reader functions for Cocktail Cabinet.

Reads and parses the Obsidian vault markdown files into structured data.
Each function corresponds to a Gemini tool declaration in declarations.py,
allowing the LLM to call them during a conversation.
"""
import re
from pathlib import Path

from src.config import OBSIDIAN_VAULT_PATH


def _read_file(filename: str) -> str:
    """Read a markdown file from the Obsidian vault.

    Args:
        filename: The markdown filename (e.g. 'Pantry.md').

    Returns:
        The file contents as a string.

    Raises:
        FileNotFoundError: If the file does not exist in the vault.
    """
    path = Path(OBSIDIAN_VAULT_PATH) / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Could not find '{filename}' in vault at {OBSIDIAN_VAULT_PATH}. "
            f"Copy the file from vault_templates/ into your vault."
        )
    return path.read_text(encoding="utf-8")


def _parse_sections(content: str) -> dict[str, list[str]]:
    """Parse a markdown file into a dict of heading -> bullet list items.

    Args:
        content: Raw markdown content.

    Returns:
        A dict mapping each ## heading to its list of bullet items.
    """
    sections: dict[str, list[str]] = {}
    current_section = None

    for line in content.splitlines():
        if line.startswith("## "):
            current_section = line[3:].strip()
            sections[current_section] = []
        elif current_section and line.startswith("- "):
            sections[current_section].append(line[2:].strip())

    return sections


def _rewrite_pantry(categories: dict[str, list[str]]) -> None:
    """Rewrite Pantry.md with a fully categorised structure.

    Args:
        categories: A dict of category name -> ingredient list.
    """
    lines = ["# Pantry", ""]
    for category, items in categories.items():
        if items:
            lines.append(f"## {category}")
            lines.extend(f"- {item}" for item in items)
            lines.append("")
    path = Path(OBSIDIAN_VAULT_PATH) / "Pantry.md"
    path.write_text("\n".join(lines), encoding="utf-8")


def read_pantry() -> dict[str, list[str]]:
    """Read and parse Pantry.md into categorised ingredients.

    If an ## Uncategorised section is found, its items are sent to
    Gemini via categorise_pantry(), merged with existing categories,
    and Pantry.md is rewritten with the organised result.

    Returns:
        A dict with category names as keys and lists of ingredients
        as values. Example::

            {
                "Spirits": ["Gin", "White rum"],
                "Mixers": ["Tonic water", "Soda water"],
                ...
            }
    """
    from src.tools.categoriser import categorise_pantry

    content = _read_file("Pantry.md")
    sections = _parse_sections(content)

    uncategorised = sections.pop("Uncategorised", [])
    if uncategorised:
        categorised = categorise_pantry(uncategorised)
        for category, items in categorised.items():
            title_key = category.title()
            existing = sections.setdefault(title_key, [])
            for item in items:
                if item not in existing:
                    existing.append(item)
        _rewrite_pantry(sections)

    return sections


def read_preferences() -> dict[str, list[str]]:
    """Read and parse Preferences.md into taste preferences.

    Returns:
        A dict with preference sections as keys and lists of items
        as values. Example::

            {
                "I like": ["Citrusy", "Refreshing"],
                "I dislike": ["Anise / liquorice", "Smoky"],
                "Preferred spirits": ["Gin", "Rum"],
                ...
            }
    """
    content = _read_file("Preferences.md")
    return _parse_sections(content)


def read_cocktail_log() -> list[dict[str, str]]:
    """Read and parse Cocktail Log.md into a list of rated cocktail entries.

    Returns:
        A list of dicts, each with 'date', 'cocktail', 'rating', and
        'notes' keys. Example::

            [
                {
                    "date": "2026-03-01",
                    "cocktail": "Gin & Tonic",
                    "rating": "⭐⭐⭐⭐",
                    "notes": "Classic, refreshing."
                },
                ...
            ]
    """
    content = _read_file("Cocktail Log.md")
    entries = []
    current: dict[str, str] = {}

    for line in content.splitlines():
        if line.startswith("### "):
            if current:
                entries.append(current)
            current = {"date": line[4:].strip()}
        elif line.startswith("**Cocktail:**"):
            current["cocktail"] = line.split("**Cocktail:**", 1)[1].strip()
        elif line.startswith("**Rating:**"):
            raw = line.split("**Rating:**", 1)[1].strip()
            current["rating"] = str(raw.count("⭐"))
        elif line.startswith("**Notes:**"):
            current["notes"] = line.split("**Notes:**", 1)[1].strip()

    if current:
        entries.append(current)

    return entries


def read_suggestions() -> list[str]:
    """Read cocktail names from Cocktail Suggestions.md.

    Parses the ### {n}. {name} headings, stripping the number, dot, and
    any badge suffix (e.g. ⭐ Best match).

    Returns:
        A list of cocktail name strings in suggestion order. Returns an
        empty list if the file is missing or contains no suggestion headings.
    """
    try:
        content = _read_file("Cocktail Suggestions.md")
    except FileNotFoundError:
        return []

    names = []
    for line in content.splitlines():
        match = re.match(r"^### \d+\.\s+(.+?)(?:\s+⭐.*)?$", line)
        if match:
            names.append(match.group(1).strip())
    return names
