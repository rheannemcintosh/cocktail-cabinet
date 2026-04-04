"""
Shopper agent for Cocktail Cabinet.

Given bartender suggestions (which include missing ingredients), this agent
classifies each missing ingredient by store accessibility tier and produces a
ranked "stock up" list of tier 1 items ordered by the number of recipes they
would unlock.

Tiers:
    1 — Any supermarket (e.g. lemons, rum, orange juice)
    2 — Larger supermarket (e.g. Angostura bitters, coconut cream)
    3 — Specialist store (e.g. rose liqueur, absinthe)
"""
import json
import re
from collections import Counter

from google.genai import types

from src.gemini_client import MODEL, _client

SYSTEM_PROMPT = """
You are a knowledgeable drinks shopper. Your job is to classify cocktail \
ingredients by how easy they are to find in shops.

Use these tiers:
- Tier 1: Available in any supermarket (e.g. lemons, limes, orange juice, \
sugar, soda water, tonic water, cola, ginger beer, mint, eggs, cream, rum, \
gin, vodka, whisky, triple sec, vermouth, prosecco)
- Tier 2: Available in a larger supermarket or well-stocked off-licence \
(e.g. Angostura bitters, Peychaud's bitters, coconut cream, grenadine, \
blue curaçao, Kahlúa, Baileys, Aperol, Campari, Midori)
- Tier 3: Requires a specialist drinks shop or online order \
(e.g. rose liqueur, absinthe, falernum, orgeat, crème de violette, \
Fernet-Branca, Chartreuse, mezcal, pisco)

You must respond with ONLY a JSON object. The keys are "tier_1", "tier_2", \
and "tier_3". Each value is a list of ingredient name strings taken exactly \
from the input list.

No explanation, no markdown, no prose — just the JSON object.
"""

_USER_PROMPT_TEMPLATE = """\
Classify each of these missing cocktail ingredients into tier 1, 2, or 3:

{ingredients}
"""


def _extract_missing_ingredients(suggestions: list[dict]) -> Counter:
    """Count how many recipes each missing ingredient appears in.

    Args:
        suggestions: List of cocktail dicts from bartender.suggest().

    Returns:
        Counter mapping ingredient name -> number of recipes it is missing from.
    """
    counter: Counter = Counter()
    for cocktail in suggestions:
        for ingredient in cocktail.get("ingredients", []):
            if not ingredient.get("in_pantry", True):
                counter[ingredient["name"]] += 1
    return counter


def _parse_tiers(text: str) -> dict[str, list[str]]:
    """Extract and parse a JSON object from the agent response.

    Args:
        text: Raw response text from the agent.

    Returns:
        Dict with keys 'tier_1', 'tier_2', 'tier_3', each a list of strings.
        Returns empty lists for all tiers if parsing fails.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {"tier_1": [], "tier_2": [], "tier_3": []}
    try:
        parsed = json.loads(match.group())
        return {
            "tier_1": parsed.get("tier_1", []),
            "tier_2": parsed.get("tier_2", []),
            "tier_3": parsed.get("tier_3", []),
        }
    except json.JSONDecodeError:
        return {"tier_1": [], "tier_2": [], "tier_3": []}


def suggest(suggestions: list[dict]) -> dict:
    """Classify missing ingredients by tier and rank tier 1 items to stock up.

    Extracts all missing ingredients from bartender suggestions, calls Gemini
    to classify them by store accessibility tier, then ranks tier 1 items by
    the number of recipes they would unlock.

    Args:
        suggestions: List of cocktail suggestion dicts from bartender.suggest(),
            each with 'name', 'ingredients' (list of {name, in_pantry}), and
            'match_score'.

    Returns:
        A dict with keys:
            - 'tier_1': list of tier 1 ingredient names
            - 'tier_2': list of tier 2 ingredient names
            - 'tier_3': list of tier 3 ingredient names
            - 'stock_up': tier 1 items sorted by recipes-unlocked count
              descending, as list of {name, recipes_unlocked} dicts

        Example::

            {
                "tier_1": ["Lemon juice", "Orange juice"],
                "tier_2": ["Angostura bitters"],
                "tier_3": ["Rose liqueur"],
                "stock_up": [
                    {"name": "Lemon juice", "recipes_unlocked": 3},
                    {"name": "Orange juice", "recipes_unlocked": 1},
                ]
            }
    """
    recipe_counts = _extract_missing_ingredients(suggestions)

    if not recipe_counts:
        return {"tier_1": [], "tier_2": [], "tier_3": [], "stock_up": []}

    ingredient_list = "\n".join(f"- {name}" for name in recipe_counts)

    chat = _client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
        ),
    )

    message = _USER_PROMPT_TEMPLATE.format(ingredients=ingredient_list)
    response = chat.send_message(message)
    tiers = _parse_tiers(response.text)

    stock_up = sorted(
        [
            {"name": name, "recipes_unlocked": recipe_counts[name]}
            for name in tiers["tier_1"]
        ],
        key=lambda x: x["recipes_unlocked"],
        reverse=True,
    )

    return {**tiers, "stock_up": stock_up}
