"""
Tests for Gemini function declarations.

Asserts that VAULT_READER_TOOL is correctly structured for use with
the Gemini generate_content tool calling API.
"""
from src.tools.declarations import VAULT_READER_TOOL

EXPECTED_FUNCTION_NAMES = {"read_pantry", "read_preferences", "read_cocktail_log"}


def test_vault_reader_tool_has_three_declarations():
    assert len(VAULT_READER_TOOL.function_declarations) == 3


def test_all_declarations_have_names():
    names = {d.name for d in VAULT_READER_TOOL.function_declarations}
    assert names == EXPECTED_FUNCTION_NAMES


def test_all_declarations_have_descriptions():
    for declaration in VAULT_READER_TOOL.function_declarations:
        assert declaration.description, f"{declaration.name} is missing a description"
