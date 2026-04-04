"""
Taste agent for Cocktail Cabinet.

Personalises bartender suggestions using the user's stated preferences and
cocktail history. Operates in two modes:

Suggestion time (filter_and_boost):
    1. Deterministically removes suggestions containing disliked ingredients.
    2. Calls Gemini to identify which remaining suggestions are most similar
       to highly-rated past cocktails and applies a score boost.

Post-rating (infer_and_update):
    Calls Gemini to infer new taste patterns from the cocktail log and merges
    them back into Preferences.md without removing existing entries.
"""
import json
import re

from google.genai import types

from src.gemini_client import MODEL, _client
from src.tools.vault_writer import write_preferences

_HIGH_RATING_THRESHOLD = 4

BOOST_SYSTEM_PROMPT = """
You are a cocktail taste analyst. Your job is to identify which cocktail \
suggestions are most similar in style, flavour, and spirit base to cocktails \
the user has rated highly in the past.

You must respond with ONLY a JSON object. The keys are cocktail names taken \
exactly from the suggestions list. Each value is a boost delta: a float \
between 0.0 and 0.2 representing how much to add to that cocktail's match \
score (0.0 means no similarity, 0.2 means very similar to a highly-rated drink).

No explanation, no markdown, no prose — just the JSON object.
"""

INFER_SYSTEM_PROMPT = """
You are a cocktail taste analyst. Your job is to study a user's cocktail \
ratings and notes and infer patterns about their taste preferences.

You must respond with ONLY a JSON object. The keys are preference section \
names (e.g. "I like", "I dislike", "Preferred spirits", "Preferred style"). \
Each value is a list of new preference strings to add — only include items \
that are not already in the current preferences and are clearly supported \
by the rating data. Do not remove or repeat existing preferences.

No explanation, no markdown, no prose — just the JSON object.
"""

_BOOST_PROMPT_TEMPLATE = """\
Highly-rated past cocktails (rating {threshold}/5 or above):
{past_cocktails}

Current suggestions to score:
{suggestions}

Return a boost delta (0.0–0.2) for each suggestion name.
"""

_INFER_PROMPT_TEMPLATE = """\
Current preferences:
{preferences}

Cocktail log (all entries):
{log}

Infer new taste preference items to add, grouped by section.
"""


def _filter_disliked(
    suggestions: list[dict], preferences: dict[str, list[str]]
) -> list[dict]:
    """Remove suggestions that contain a disliked ingredient.

    Performs a case-insensitive substring match between each ingredient name
    and each item in the "I dislike" section of preferences.

    Args:
        suggestions: List of cocktail dicts from bartender.suggest().
        preferences: Preferences dict from read_preferences().

    Returns:
        Filtered list with any suggestion containing a disliked ingredient removed.
    """
    disliked = [d.lower() for d in preferences.get("I dislike", [])]
    if not disliked:
        return suggestions

    filtered = []
    for cocktail in suggestions:
        ingredient_names = [
            ing["name"].lower() for ing in cocktail.get("ingredients", [])
        ]
        if not any(
            dislike in ingredient for dislike in disliked for ingredient in ingredient_names
        ):
            filtered.append(cocktail)
    return filtered


def _parse_boosts(text: str) -> dict[str, float]:
    """Extract and parse a JSON object of boost deltas from the agent response.

    Args:
        text: Raw response text from the agent.

    Returns:
        Dict mapping cocktail name to boost delta float.
        Returns an empty dict if parsing fails.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def _parse_preference_updates(text: str) -> dict[str, list[str]]:
    """Extract and parse a JSON object of preference updates from the agent response.

    Args:
        text: Raw response text from the agent.

    Returns:
        Dict mapping section name to list of new preference strings.
        Returns an empty dict if parsing fails.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return {}


def filter_and_boost(
    suggestions: list[dict],
    preferences: dict[str, list[str]],
    cocktail_log: list[dict],
) -> list[dict]:
    """Filter disliked suggestions and boost scores based on past highly-rated cocktails.

    First removes any suggestions whose ingredients overlap with the "I dislike"
    section of preferences. Then calls Gemini with the user's highly-rated log
    entries to identify stylistically similar suggestions and applies a score boost
    (capped at 1.0). Returns suggestions re-sorted by adjusted score.

    If there are no highly-rated log entries the boost step is skipped and the
    filtered list is returned as-is.

    Args:
        suggestions: List of cocktail dicts from bartender.suggest().
        preferences: Preferences dict from read_preferences().
        cocktail_log: List of log entry dicts from read_cocktail_log().

    Returns:
        Filtered and re-sorted list of cocktail dicts. Each dict has the same
        shape as bartender output ('name', 'ingredients', 'match_score') with
        match_score potentially boosted. Example::

            [
                {
                    "name": "Gimlet",
                    "ingredients": [{"name": "Gin", "in_pantry": True}, ...],
                    "match_score": 0.95,
                },
                ...
            ]
    """
    filtered = _filter_disliked(suggestions, preferences)

    if not filtered:
        return filtered

    high_rated = [
        entry for entry in cocktail_log
        if int(entry.get("rating", 0)) >= _HIGH_RATING_THRESHOLD
    ]

    if not high_rated:
        return filtered

    past_cocktails = "\n".join(
        f"- {e['cocktail']} (rated {e['rating']}/5)"
        + (f": {e['notes']}" if e.get("notes") else "")
        for e in high_rated
    )
    suggestion_names = "\n".join(f"- {c['name']}" for c in filtered)

    chat = _client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(system_instruction=BOOST_SYSTEM_PROMPT),
    )
    message = _BOOST_PROMPT_TEMPLATE.format(
        threshold=_HIGH_RATING_THRESHOLD,
        past_cocktails=past_cocktails,
        suggestions=suggestion_names,
    )
    response = chat.send_message(message)
    boosts = _parse_boosts(response.text)

    boosted = []
    for cocktail in filtered:
        delta = boosts.get(cocktail["name"], 0.0)
        boosted.append({
            **cocktail,
            "match_score": min(1.0, cocktail["match_score"] + delta),
        })

    return sorted(boosted, key=lambda c: c["match_score"], reverse=True)


def infer_and_update(
    cocktail_log: list[dict],
    preferences: dict[str, list[str]],
) -> str:
    """Infer new taste patterns from the cocktail log and update Preferences.md.

    Calls Gemini with the full cocktail log and current preferences to identify
    taste patterns supported by the rating data. Merges any new inferences into
    the existing preferences dict without removing current entries, then writes
    the result back to Preferences.md.

    If the log is empty, no Gemini call is made and a no-op message is returned.

    Args:
        cocktail_log: List of log entry dicts from read_cocktail_log().
        preferences: Current preferences dict from read_preferences().

    Returns:
        A summary string describing what was inferred and updated.
    """
    if not cocktail_log:
        return "No cocktail log entries — preferences unchanged."

    log_text = "\n".join(
        f"- {e['cocktail']} (rated {e['rating']}/5)"
        + (f": {e['notes']}" if e.get("notes") else "")
        for e in cocktail_log
    )
    preferences_text = "\n".join(
        f"{section}:\n" + "\n".join(f"  - {item}" for item in items)
        for section, items in preferences.items()
    )

    chat = _client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(system_instruction=INFER_SYSTEM_PROMPT),
    )
    message = _INFER_PROMPT_TEMPLATE.format(
        preferences=preferences_text,
        log=log_text,
    )
    response = chat.send_message(message)
    updates = _parse_preference_updates(response.text)

    if not updates:
        return "No new taste patterns inferred — preferences unchanged."

    merged = {section: list(items) for section, items in preferences.items()}
    added: dict[str, list[str]] = {}

    for section, new_items in updates.items():
        existing = [item.lower() for item in merged.get(section, [])]
        to_add = [item for item in new_items if item.lower() not in existing]
        if to_add:
            merged.setdefault(section, []).extend(to_add)
            added[section] = to_add

    write_preferences(merged)

    if not added:
        return "No new taste patterns inferred — preferences unchanged."

    summary_lines = ["Preferences updated:"]
    for section, items in added.items():
        summary_lines.append(f"  {section}: added {', '.join(items)}")
    return "\n".join(summary_lines)
