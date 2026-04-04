"""
Prompt orchestration chain for Cocktail Cabinet.

Implements the chain where each step's output feeds into the next as
context. This is the "prompt orchestration" LLM integration pattern —
demonstrating how chained prompts build up rich context across steps.

Chain:
    1. Read vault — pantry, preferences, cocktail log
    2. Map mood to flavour profile
    3. Pass pantry + flavour profile to the bartender agent
    4. Pass bartender suggestions to the shopper agent
    5. Format agent output as markdown for the vault
"""
from src import agents
from src.agents import bartender, shopper
from src.mood import map_mood_to_flavour
from src.tools.vault_reader import read_cocktail_log, read_pantry, read_preferences


def _format_suggestions(suggestions: list[dict], mood: str) -> str:
    """Format the bartender agent's structured output as vault markdown.

    Args:
        suggestions: List of cocktail dicts from bartender.suggest().
        mood: The user's original mood string.

    Returns:
        Formatted markdown string ready to write to Cocktail Suggestions.md.
    """
    lines = [
        "# Cocktail Suggestions",
        "",
        f"_Refreshed each time Cocktail Cabinet runs._",
        "",
        "---",
        "",
        f"## Tonight's suggestions for mood: {mood}",
        "",
    ]

    for i, cocktail in enumerate(suggestions, start=1):
        match_pct = int(cocktail["match_score"] * 100)
        missing = [ing for ing in cocktail["ingredients"] if not ing["in_pantry"]]
        badge = " ⭐ Best match" if i == 1 else ""
        lines.append(f"### {i}. {cocktail['name']}{badge}")

        if not missing:
            lines.append("**You have everything.**")
        else:
            lines.append(f"**Missing {len(missing)} ingredient(s).**")

        lines.append("")
        lines.append("| Ingredient | In pantry |")
        lines.append("|---|---|")
        for ing in cocktail["ingredients"]:
            status = "✅" if ing["in_pantry"] else "❌"
            lines.append(f"| {ing['name']} | {status} |")

        lines.extend(["", f"_Match: {match_pct}%_", "", "---", ""])

    lines.extend([
        "## Rate tonight's cocktail",
        "_Add your rating to [[Cocktail Log]] once you've made your choice._",
    ])

    return "\n".join(lines)


def _format_shopping_list(shopping: dict) -> str:
    """Format the shopper agent's structured output as a markdown section.

    Args:
        shopping: Dict from shopper.suggest() with keys 'tier_1', 'tier_2',
            'tier_3', and 'stock_up'.

    Returns:
        Formatted markdown string for the shopping list section.
    """
    lines = [
        "---",
        "",
        "## Shopping list",
        "",
    ]

    stock_up = shopping.get("stock_up", [])
    if stock_up:
        lines.append("### Stock up (any supermarket)")
        lines.append("_These tier 1 items unlock the most recipes:_")
        lines.append("")
        for item in stock_up:
            lines.append(f"- {item['name']} _(unlocks {item['recipes_unlocked']} recipe(s))_")
        lines.append("")

    tier_2 = shopping.get("tier_2", [])
    if tier_2:
        lines.append("### Larger supermarket")
        for item in tier_2:
            lines.append(f"- {item}")
        lines.append("")

    tier_3 = shopping.get("tier_3", [])
    if tier_3:
        lines.append("### Specialist store")
        for item in tier_3:
            lines.append(f"- {item}")
        lines.append("")

    if not stock_up and not tier_2 and not tier_3:
        lines.append("_Nothing to buy — you have everything you need._")
        lines.append("")

    return "\n".join(lines)


def run(mood: str) -> str:
    """Run the prompt orchestration chain and return cocktail suggestions.

    Executes the chain in sequence, passing each step's output into
    the next as context:

    1. Read pantry, preferences, and cocktail log from the vault.
    2. Map the mood to a structured flavour profile via Gemini.
    3. Pass pantry and flavour profile to the bartender agent.
    4. Pass bartender suggestions to the shopper agent.
    5. Format the agents' structured output as markdown.

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

    # Step 3: Bartender agent — ranked cocktail suggestions
    suggestions = bartender.suggest(pantry, flavour_profile)

    # Step 4: Shopper agent — classify missing ingredients and rank stock-up list
    shopping = shopper.suggest(suggestions)

    # Step 5: Format for vault
    return _format_suggestions(suggestions, mood) + "\n" + _format_shopping_list(shopping)
