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
        from src.config import OBSIDIAN_VAULT_PATH
    except EnvironmentError as e:
        print(f"Configuration error: {e}")
        raise SystemExit(1)

    print(f"Finding cocktails for mood: {args.mood}")
    print(f"Vault: {OBSIDIAN_VAULT_PATH}")
    print("(Suggestions coming soon...)")


if __name__ == "__main__":
    main()
