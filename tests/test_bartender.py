"""
Tests for the bartender agent.

Mocks the Gemini chat to avoid live API calls and verify that the
system prompt is set, input context is passed correctly, and the
response is parsed into a structured list.
"""
import json
from unittest.mock import MagicMock

import pytest

import src.agents.bartender as bartender_module
from src.agents.bartender import suggest

PANTRY = {
    "Spirits": ["Gin", "White rum"],
    "Mixers": ["Tonic water", "Soda water"],
    "Juices": ["Lime juice"],
    "Syrups": ["Simple syrup"],
}

FLAVOUR_PROFILE = {
    "flavour_notes": ["citrus", "light"],
    "preferred_spirits": ["gin"],
    "style": "long",
    "avoid": ["smoky"],
}

MOCK_SUGGESTIONS = [
    {
        "name": "Gin & Tonic",
        "ingredients": [
            {"name": "Gin", "in_pantry": True},
            {"name": "Tonic water", "in_pantry": True},
        ],
        "match_score": 1.0,
    },
    {
        "name": "Mojito",
        "ingredients": [
            {"name": "White rum", "in_pantry": True},
            {"name": "Lime juice", "in_pantry": True},
            {"name": "Mint", "in_pantry": False},
        ],
        "match_score": 0.67,
    },
]


@pytest.fixture
def mock_chat(mocker):
    """Mock _client at module level to avoid patching SDK properties."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(MOCK_SUGGESTIONS)

    mock_chat_session = MagicMock()
    mock_chat_session.send_message.return_value = mock_response

    mock_client = MagicMock()
    mock_client.chats.create.return_value = mock_chat_session

    mocker.patch.object(bartender_module, "_client", mock_client)
    return mock_client


class TestSuggest:
    def test_creates_chat_with_system_prompt(self, mock_chat):
        suggest(PANTRY, FLAVOUR_PROFILE)
        call_kwargs = mock_chat.create.call_args[1]
        system_instruction = call_kwargs["config"].system_instruction
        assert system_instruction == bartender_module.SYSTEM_PROMPT

    def test_message_contains_pantry_ingredients(self, mock_chat):
        suggest(PANTRY, FLAVOUR_PROFILE)
        message = mock_chat.create.return_value.send_message.call_args[0][0]
        assert "Gin" in message
        assert "White rum" in message

    def test_message_contains_flavour_profile(self, mock_chat):
        suggest(PANTRY, FLAVOUR_PROFILE)
        message = mock_chat.create.return_value.send_message.call_args[0][0]
        assert "citrus" in message

    def test_returns_list_of_suggestions(self, mock_chat):
        result = suggest(PANTRY, FLAVOUR_PROFILE)
        assert isinstance(result, list)
        assert len(result) == 2

    def test_suggestions_have_required_keys(self, mock_chat):
        result = suggest(PANTRY, FLAVOUR_PROFILE)
        for suggestion in result:
            assert "name" in suggestion
            assert "ingredients" in suggestion
            assert "match_score" in suggestion

    def test_suggestions_sorted_by_match_score_descending(self, mock_chat):
        result = suggest(PANTRY, FLAVOUR_PROFILE)
        scores = [s["match_score"] for s in result]
        assert scores == sorted(scores, reverse=True)

    def test_raises_value_error_on_unparseable_response(self, mock_chat):
        mock_chat.create.return_value.send_message.return_value.text = "Sorry, I cannot help."
        with pytest.raises(ValueError):
            suggest(PANTRY, FLAVOUR_PROFILE)
