"""
Pantry categoriser for Cocktail Cabinet.

Uses a Gemini prompt call to auto-categorise a flat list of ingredients
into structured categories. This is part of the prompt orchestration
pattern — the output feeds into the pantry reader so users can dump
ingredients into Pantry.md unstructured and have them organised automatically.
"""
import json
import re

from src.gemini_client import generate

CATEGORIES = [
    "spirits",
    "liqueurs",
    "mixers",
    "juices",
    "syrups",
    "bitters",
    "garnishes",
    "other",
]

_PROMPT_TEMPLATE = """\
You are a bartender's assistant. Categorise the following ingredients into \
these categories: {categories}.

Return ONLY a JSON object where each key is a category name and each value \
is a list of ingredient strings. Include only categories that have at least \
one ingredient. Do not include any explanation or markdown — just the JSON.

Ingredients:
{ingredients}
"""


def _parse_json(text: str) -> dict[str, list[str]]:
    """Extract and parse a JSON object from a Gemini response string.

    Strips markdown code fences if present before parsing.

    Args:
        text: Raw response text from Gemini.

    Returns:
        Parsed dict of category -> ingredient list.

    Raises:
        ValueError: If no valid JSON object can be parsed from the response.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in Gemini response: {text!r}")
    return json.loads(match.group())


def categorise_pantry(items: list[str]) -> dict[str, list[str]]:
    """Categorise a flat list of ingredients using Gemini.

    Sends the ingredient list to Gemini with a structured prompt and
    parses the JSON response into a category dict. Unknown ingredients
    are placed in the 'other' category.

    Args:
        items: A flat list of ingredient names, e.g. ['Gin', 'Lemon juice',
            'Angostura bitters'].

    Returns:
        A dict mapping category names to lists of ingredients, e.g.::

            {
                "spirits": ["Gin"],
                "juices": ["Lemon juice"],
                "bitters": ["Angostura bitters"]
            }

    Raises:
        ValueError: If Gemini returns a response that cannot be parsed as JSON.
    """
    prompt = _PROMPT_TEMPLATE.format(
        categories=", ".join(CATEGORIES),
        ingredients="\n".join(f"- {item}" for item in items),
    )
    response = generate(prompt)
    return _parse_json(response)
