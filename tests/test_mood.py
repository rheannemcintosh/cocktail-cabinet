"""
Tests for mood-to-flavour mapping.

Mocks the Gemini generate() call to avoid live API calls in unit tests.
"""
import json

import pytest

import src.mood as mood_module
from src.mood import map_mood_to_flavour


@pytest.fixture
def mock_generate(mocker):
    """Mock gemini_client.generate() in the mood module."""
    return mocker.patch.object(mood_module, "generate")


@pytest.fixture
def valid_flavour_profile():
    return {
        "flavour_notes": ["citrus", "light"],
        "preferred_spirits": ["gin", "vodka"],
        "style": "long",
        "avoid": ["smoky", "heavy"],
    }


class TestMapMoodToFlavour:
    def test_prompt_contains_mood(self, mock_generate, valid_flavour_profile):
        mock_generate.return_value = json.dumps(valid_flavour_profile)
        map_mood_to_flavour("refreshing")
        prompt = mock_generate.call_args[0][0]
        assert "refreshing" in prompt

    def test_returns_parsed_dict(self, mock_generate, valid_flavour_profile):
        mock_generate.return_value = json.dumps(valid_flavour_profile)
        result = map_mood_to_flavour("refreshing")
        assert isinstance(result, dict)
        assert result["flavour_notes"] == ["citrus", "light"]
        assert result["style"] == "long"

    def test_handles_json_wrapped_in_code_fence(self, mock_generate, valid_flavour_profile):
        mock_generate.return_value = (
            "```json\n" + json.dumps(valid_flavour_profile) + "\n```"
        )
        result = map_mood_to_flavour("cosy")
        assert result["preferred_spirits"] == ["gin", "vodka"]

    def test_raises_value_error_on_unparseable_response(self, mock_generate):
        mock_generate.return_value = "I cannot map that mood."
        with pytest.raises(ValueError):
            map_mood_to_flavour("something")
