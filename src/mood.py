"""
Mood-to-flavour mapping for Cocktail Cabinet.

The first step in the prompt orchestration chain — maps a free-text mood
string to a structured flavour profile that guides recipe selection.
The output feeds directly into the context assembly step.
"""
import json
import re

from src.gemini_client import generate

_PROMPT_TEMPLATE = """\
You are a bartender's assistant. A customer says they are in the mood for \
something "{mood}".

Map this mood to a cocktail flavour profile. Return ONLY a JSON object with \
these keys:
- "flavour_notes": list of flavour descriptors (e.g. "citrus", "sweet", "herbal")
- "preferred_spirits": list of spirit types that suit this mood (e.g. "gin", "rum")
- "style": one of "long", "short", "shot", or "any"
- "avoid": list of flavours or ingredients to avoid for this mood

Do not include any explanation or markdown — just the JSON.
"""


def _parse_json(text: str) -> dict:
    """Extract and parse a JSON object from a Gemini response string.

    Args:
        text: Raw response text from Gemini.

    Returns:
        Parsed flavour profile dict.

    Raises:
        ValueError: If no valid JSON object can be parsed from the response.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON object found in Gemini response: {text!r}")
    return json.loads(match.group())


def map_mood_to_flavour(mood: str) -> dict:
    """Map a free-text mood to a structured cocktail flavour profile.

    Sends the mood to Gemini and returns a JSON flavour profile. The
    result is used in the next orchestration step to guide recipe
    selection towards drinks that suit how the user is feeling.

    Args:
        mood: A free-text mood description, e.g. "refreshing", "cosy",
            "tropical", "indulgent".

    Returns:
        A dict with keys: flavour_notes, preferred_spirits, style, avoid.
        Example::

            {
                "flavour_notes": ["citrus", "light", "effervescent"],
                "preferred_spirits": ["gin", "vodka", "white rum"],
                "style": "long",
                "avoid": ["smoky", "heavy", "sweet"]
            }

    Raises:
        ValueError: If Gemini returns a response that cannot be parsed as JSON.
    """
    prompt = _PROMPT_TEMPLATE.format(mood=mood)
    response = generate(prompt)
    return _parse_json(response)
