"""
Tests for Gemini function declarations.

Asserts that VAULT_TOOLS is correctly structured for use with
the Gemini generate_content tool calling API.
"""
from src.tools.declarations import VAULT_TOOLS

EXPECTED_FUNCTION_NAMES = {
    "read_pantry",
    "read_preferences",
    "read_cocktail_log",
    "write_suggestion",
    "write_to_log",
}


def test_vault_tools_has_five_declarations():
    assert len(VAULT_TOOLS.function_declarations) == 5


def test_all_declarations_have_names():
    names = {d.name for d in VAULT_TOOLS.function_declarations}
    assert names == EXPECTED_FUNCTION_NAMES


def test_all_declarations_have_descriptions():
    for declaration in VAULT_TOOLS.function_declarations:
        assert declaration.description, f"{declaration.name} is missing a description"
