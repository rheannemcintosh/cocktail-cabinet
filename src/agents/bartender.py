"""
Bartender agent for Cocktail Cabinet.

The first specialist agent in the multi-agent planning pattern. Given a
categorised pantry and a mood/flavour profile, the agent suggests 2-3
cocktails ranked by how many ingredients the user already has. Its
structured output feeds into the shopper and taste agents.
"""
import json
import re

from google.genai import types

from src.gemini_client import MODEL, _client

SYSTEM_PROMPT = """
You are an expert bartender with deep knowledge of classic and contemporary \
cocktails. Your job is to suggest cocktails based on what a customer has in \
their home bar and what they are in the mood for tonight.

Your priorities:
1. Suggest cocktails the customer can make right now with what they have.
2. Include one or two "nearly there" options that require only 1-2 missing \
ingredients.
3. Rank suggestions by match score — the proportion of required ingredients \
already in the pantry.
4. Never suggest cocktails that require more than 2 missing ingredients.

You must respond with ONLY a JSON array. Each element must have:
- "name": cocktail name (string)
- "ingredients": list of objects with "name" (string) and "in_pantry" (bool)
- "match_score": number of pantry ingredients / total ingredients, as a float \
rounded to 2 decimal places

No explanation, no markdown, no prose — just the JSON array.
"""

_USER_PROMPT_TEMPLATE = """\
Pantry:
{pantry}

Mood and flavour profile:
{flavour_profile}

Suggest 2-3 cocktails.
"""


def _format_pantry(pantry: dict[str, list[str]]) -> str:
    """Format pantry dict as a flat ingredient list for the prompt."""
    items = [item for ingredients in pantry.values() for item in ingredients]
    return "\n".join(f"- {item}" for item in items)


def _parse_suggestions(text: str) -> list[dict]:
    """Extract and parse a JSON array from the agent response.

    Args:
        text: Raw response text from the agent.

    Returns:
        Parsed list of cocktail suggestion dicts.

    Raises:
        ValueError: If no valid JSON array can be parsed from the response.
    """
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in agent response: {text!r}")
    return json.loads(match.group())


def suggest(pantry: dict[str, list[str]], flavour_profile: dict) -> list[dict]:
    """Suggest cocktails ranked by pantry ingredient availability.

    Initialises a Gemini chat session with the bartender system prompt
    and sends the pantry and flavour profile as context. Returns a
    structured list of suggestions ready to pass to the shopper and
    taste agents.

    Args:
        pantry: Categorised pantry dict from read_pantry().
        flavour_profile: Flavour profile dict from map_mood_to_flavour().

    Returns:
        A list of cocktail suggestion dicts, each with 'name',
        'ingredients' (list of {name, in_pantry}), and 'match_score'.
        Sorted by match_score descending. Example::

            [
                {
                    "name": "Daiquiri",
                    "ingredients": [
                        {"name": "White rum", "in_pantry": True},
                        {"name": "Lime juice", "in_pantry": True},
                        {"name": "Simple syrup", "in_pantry": True}
                    ],
                    "match_score": 1.0
                },
                ...
            ]

    Raises:
        ValueError: If the agent returns a response that cannot be parsed.
    """
    chat = _client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )

    message = _USER_PROMPT_TEMPLATE.format(
        pantry=_format_pantry(pantry),
        flavour_profile=json.dumps(flavour_profile, indent=2),
    )

    response = chat.send_message(message)
    suggestions = _parse_suggestions(response.text)
    return sorted(suggestions, key=lambda s: s.get("match_score", 0), reverse=True)
