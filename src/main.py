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
    args = parser.parse_args()

    try:
        from src.config import GEMINI_API_KEY, OBSIDIAN_VAULT_PATH
    except EnvironmentError as e:
        print(f"Configuration error: {e}")
        raise SystemExit(1)

    from src.orchestrator import run, update_preferences
    from src.tools.vault_writer import write_suggestion

    result = run(args.mood)
    print("→ Writing up tonight's suggestions...")
    confirmation = write_suggestion(result)
    print(confirmation)

    preference_summary = update_preferences()
    print(preference_summary)


if __name__ == "__main__":
    main()
