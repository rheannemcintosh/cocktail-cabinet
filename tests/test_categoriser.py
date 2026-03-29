"""
Tests for the pantry categoriser.

Mocks the Gemini generate() call to avoid live API calls in unit tests.
"""
import json

import pytest

import src.tools.categoriser as categoriser_module
from src.tools.categoriser import categorise_pantry


@pytest.fixture
def mock_generate(mocker):
    """Mock gemini_client.generate() in the categoriser module."""
    return mocker.patch.object(categoriser_module, "generate")


class TestCategorisePantry:
    def test_sends_prompt_containing_ingredients(self, mock_generate):
        mock_generate.return_value = json.dumps({"spirits": ["Gin"]})
        categorise_pantry(["Gin"])
        prompt = mock_generate.call_args[0][0]
        assert "Gin" in prompt

    def test_prompt_contains_all_categories(self, mock_generate):
        mock_generate.return_value = json.dumps({"spirits": ["Gin"]})
        categorise_pantry(["Gin"])
        prompt = mock_generate.call_args[0][0]
        for category in categoriser_module.CATEGORIES:
            assert category in prompt

    def test_returns_parsed_category_dict(self, mock_generate):
        mock_generate.return_value = json.dumps({
            "spirits": ["Gin", "Vodka"],
            "mixers": ["Tonic water"],
        })
        result = categorise_pantry(["Gin", "Vodka", "Tonic water"])
        assert result["spirits"] == ["Gin", "Vodka"]
        assert result["mixers"] == ["Tonic water"]

    def test_handles_json_wrapped_in_code_fence(self, mock_generate):
        mock_generate.return_value = (
            "```json\n" + json.dumps({"bitters": ["Angostura bitters"]}) + "\n```"
        )
        result = categorise_pantry(["Angostura bitters"])
        assert result["bitters"] == ["Angostura bitters"]

    def test_raises_value_error_on_unparseable_response(self, mock_generate):
        mock_generate.return_value = "Sorry, I cannot categorise these."
        with pytest.raises(ValueError):
            categorise_pantry(["something"])
