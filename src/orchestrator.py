"""
Prompt orchestration chain for Cocktail Cabinet.

Implements the four-step chain where each step's output feeds into the
next as context. This is the "prompt orchestration" LLM integration
pattern — demonstrating how chained prompts can build up rich context
for a final generation step.

Chain:
    1. Read vault — pantry, preferences, cocktail log
    2. Map mood to flavour profile
    3. Assemble structured context from all step outputs
    4. Send context to Gemini for recipe generation
"""
import json

from src.gemini_client import generate
from src.mood import map_mood_to_flavour
from src.tools.vault_reader import read_cocktail_log, read_pantry, read_preferences

_RECIPE_PROMPT_TEMPLATE = """\
You are an expert bartender. Suggest 2-3 cocktails based on the following \
context.

## Pantry
{pantry}

## Taste preferences
{preferences}

## Past cocktails (with ratings)
{cocktail_log}

## Tonight's mood
The user is feeling: {mood}

Flavour profile for this mood:
{flavour_profile}

## Instructions
- Prioritise cocktails the user can make with what they have.
- For each suggestion, list the ingredients and mark any that are missing.
- For missing ingredients, add an accessibility tier:
  - Tier 1: any supermarket
  - Tier 2: larger supermarket
  - Tier 3: specialist shop
- Avoid ingredients the user dislikes.
- Favour cocktails similar to ones they have rated highly.
- Format the output as clean markdown, ready to save to an Obsidian note.
"""


def _format_pantry(pantry: dict[str, list[str]]) -> str:
    """Format the pantry dict as a readable string for the prompt."""
    lines = []
    for category, items in pantry.items():
        if items:
            lines.append(f"{category}: {', '.join(items)}")
    return "\n".join(lines)


def _format_preferences(preferences: dict[str, list[str]]) -> str:
    """Format the preferences dict as a readable string for the prompt."""
    lines = []
    for section, items in preferences.items():
        if items:
            lines.append(f"{section}: {', '.join(items)}")
    return "\n".join(lines)


def _format_cocktail_log(log: list[dict[str, str]]) -> str:
    """Format the cocktail log as a readable string for the prompt."""
    if not log:
        return "No cocktails logged yet."
    lines = []
    for entry in log:
        stars = "⭐" * int(entry.get("rating", 0))
        lines.append(f"- {entry['cocktail']} {stars}: {entry.get('notes', '')}")
    return "\n".join(lines)


def run(mood: str) -> str:
    """Run the prompt orchestration chain and return cocktail suggestions.

    Executes four steps in sequence, passing each step's output into
    the next as context:

    1. Read pantry, preferences, and cocktail log from the vault.
    2. Map the mood to a structured flavour profile via Gemini.
    3. Assemble all context into a single structured prompt.
    4. Send the prompt to Gemini and return the suggestion text.

    Args:
        mood: A free-text mood description from the user, e.g. "refreshing".

    Returns:
        Formatted markdown suggestion text ready to write to the vault.
    """
    # Step 1: Read vault
    pantry = read_pantry()
    preferences = read_preferences()
    cocktail_log = read_cocktail_log()

    # Step 2: Map mood to flavour profile
    flavour_profile = map_mood_to_flavour(mood)

    # Step 3: Assemble context
    prompt = _RECIPE_PROMPT_TEMPLATE.format(
        pantry=_format_pantry(pantry),
        preferences=_format_preferences(preferences),
        cocktail_log=_format_cocktail_log(cocktail_log),
        mood=mood,
        flavour_profile=json.dumps(flavour_profile, indent=2),
    )

    # Step 4: Generate suggestions
    return generate(prompt)
