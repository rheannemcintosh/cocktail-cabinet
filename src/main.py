"""
CLI entry point for Cocktail Cabinet.

Parses the --mood argument and runs the suggestion pipeline.
"""
import argparse


def _prompt_to_log(suggestions: list[str]) -> None:
    """Prompt the user to log the cocktail they made tonight.

    Prints a numbered list of suggestion names and asks for a selection.
    If a valid number is chosen, prompts for a rating (1-5) and optional
    notes, then writes the entry to the cocktail log.

    Args:
        suggestions: Ordered list of cocktail names from the suggestion run.
    """
    if not suggestions:
        return

    from src.tools.vault_writer import write_to_log

    print("\nWhich cocktail did you make tonight?")
    for i, name in enumerate(suggestions, start=1):
        print(f"  {i}. {name}")
    print("  (Enter to skip)")

    raw = input("> ").strip()
    if not raw:
        return

    try:
        choice = int(raw)
        if choice < 1 or choice > len(suggestions):
            raise ValueError
    except ValueError:
        print("No cocktail logged.")
        return

    cocktail = suggestions[choice - 1]

    while True:
        rating_raw = input(f"Rating for {cocktail} (1–5): ").strip()
        try:
            rating = int(rating_raw)
            if 1 <= rating <= 5:
                break
        except ValueError:
            pass
        print("Please enter a number between 1 and 5.")

    notes = input("Notes (optional, Enter to skip): ").strip()

    confirmation = write_to_log(cocktail, rating, notes or "")
    print(confirmation)


def main() -> None:
    """Run the Cocktail Cabinet CLI.

    Parses the --mood argument, loads config, runs the full agent chain,
    writes suggestions to the vault, and updates taste preferences from
    any new cocktail log ratings.
    """
    parser = argparse.ArgumentParser(description="Cocktail Cabinet — suggest cocktails based on your mood.")
    parser.add_argument("--mood", required=True, help="How you're feeling (e.g. 'refreshing', 'cosy', 'tropical')")
    parser.add_argument("--verbose", action="store_true", help="Print key inputs and outputs at each agent boundary")
    args = parser.parse_args()

    try:
        from src.config import GEMINI_API_KEY, OBSIDIAN_VAULT_PATH
    except EnvironmentError as e:
        print(f"Configuration error: {e}")
        raise SystemExit(1)

    from src.orchestrator import run, update_preferences
    from src.tools.vault_reader import read_suggestions
    from src.tools.vault_writer import write_suggestion

    result = run(args.mood, verbose=args.verbose)
    print("→ Writing up tonight's suggestions...")
    confirmation = write_suggestion(result)
    print(confirmation)

    _prompt_to_log(read_suggestions())

    preference_summary = update_preferences(verbose=args.verbose)
    print(preference_summary)


if __name__ == "__main__":
    main()
