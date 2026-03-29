"""
CLI entry point for Cocktail Cabinet.

Parses the --mood argument and runs the suggestion pipeline.
"""
import argparse


def main() -> None:
    """Run the Cocktail Cabinet CLI.

    Parses the --mood argument, loads config, and prints cocktail
    suggestions based on the user's pantry and preferences.
    """
    parser = argparse.ArgumentParser(description="Cocktail Cabinet — suggest cocktails based on your mood.")
    parser.add_argument("--mood", required=True, help="How you're feeling (e.g. 'refreshing', 'cosy', 'tropical')")
    args = parser.parse_args()

    try:
        from src.config import GEMINI_API_KEY, OBSIDIAN_VAULT_PATH
    except EnvironmentError as e:
        print(f"Configuration error: {e}")
        raise SystemExit(1)

    from src.orchestrator import run
    result = run(args.mood)
    print(result)


if __name__ == "__main__":
    main()
