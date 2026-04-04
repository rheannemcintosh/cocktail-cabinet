"""
CLI entry point for Cocktail Cabinet.

Parses the --mood argument and runs the suggestion pipeline.
"""
import argparse


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
    from src.tools.vault_writer import write_suggestion

    result = run(args.mood, verbose=args.verbose)
    print("→ Writing up tonight's suggestions...")
    confirmation = write_suggestion(result)
    print(confirmation)

    preference_summary = update_preferences(verbose=args.verbose)
    print(preference_summary)


if __name__ == "__main__":
    main()
