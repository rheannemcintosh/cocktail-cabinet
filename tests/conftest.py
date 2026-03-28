"""
Pytest configuration and shared fixtures.

Loads .env first so real values take precedence, then falls back to
test placeholders so config.py does not raise on missing vars.
"""
import os

from dotenv import load_dotenv

load_dotenv()

os.environ.setdefault("GEMINI_API_KEY", "test-api-key")
os.environ.setdefault("OBSIDIAN_VAULT_PATH", "/fake/vault/path")
