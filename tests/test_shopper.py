"""
Tests for the shopper agent.

Mocks the Gemini chat to avoid live API calls and verify that the system
prompt is set, input context is passed correctly, tier classification is
parsed, and the stock-up list is ranked correctly.
"""
import json
from unittest.mock import MagicMock

import pytest

import src.agents.shopper as shopper_module
from src.agents.shopper import _extract_missing_ingredients, _parse_tiers, suggest

SUGGESTIONS = [
    {
        "name": "Daiquiri",
        "ingredients": [
            {"name": "White rum", "in_pantry": True},
            {"name": "Lime juice", "in_pantry": True},
            {"name": "Simple syrup", "in_pantry": False},
        ],
        "match_score": 0.67,
    },
    {
        "name": "Jungle Bird",
        "ingredients": [
            {"name": "Dark rum", "in_pantry": True},
            {"name": "Campari", "in_pantry": True},
            {"name": "Simple syrup", "in_pantry": False},
            {"name": "Pineapple juice", "in_pantry": False},
        ],
        "match_score": 0.5,
    },
    {
        "name": "Corpse Reviver No.2",
        "ingredients": [
            {"name": "Gin", "in_pantry": True},
            {"name": "Triple sec", "in_pantry": True},
            {"name": "Lemon juice", "in_pantry": False},
            {"name": "Absinthe", "in_pantry": False},
        ],
        "match_score": 0.5,
    },
]

MOCK_TIERS = {
    "tier_1": ["Simple syrup", "Pineapple juice", "Lemon juice"],
    "tier_2": [],
    "tier_3": ["Absinthe"],
}


@pytest.fixture
def mock_chat(mocker):
    """Mock _client at module level to avoid patching SDK properties."""
    mock_response = MagicMock()
    mock_response.text = json.dumps(MOCK_TIERS)

    mock_chat_session = MagicMock()
    mock_chat_session.send_message.return_value = mock_response

    mock_client = MagicMock()
    mock_client.chats.create.return_value = mock_chat_session

    mocker.patch.object(shopper_module, "_client", mock_client)
    return mock_client


class TestExtractMissingIngredients:
    def test_counts_missing_ingredients(self):
        counts = _extract_missing_ingredients(SUGGESTIONS)
        assert counts["Simple syrup"] == 2
        assert counts["Pineapple juice"] == 1
        assert counts["Lemon juice"] == 1
        assert counts["Absinthe"] == 1

    def test_excludes_pantry_ingredients(self):
        counts = _extract_missing_ingredients(SUGGESTIONS)
        assert "White rum" not in counts
        assert "Gin" not in counts

    def test_empty_suggestions_returns_empty_counter(self):
        counts = _extract_missing_ingredients([])
        assert len(counts) == 0

    def test_all_pantry_returns_empty_counter(self):
        all_in_pantry = [
            {
                "name": "Gin & Tonic",
                "ingredients": [
                    {"name": "Gin", "in_pantry": True},
                    {"name": "Tonic water", "in_pantry": True},
                ],
                "match_score": 1.0,
            }
        ]
        counts = _extract_missing_ingredients(all_in_pantry)
        assert len(counts) == 0


class TestParseTiers:
    def test_parses_valid_json_object(self):
        text = json.dumps(MOCK_TIERS)
        result = _parse_tiers(text)
        assert result["tier_1"] == MOCK_TIERS["tier_1"]
        assert result["tier_2"] == []
        assert result["tier_3"] == MOCK_TIERS["tier_3"]

    def test_parses_json_in_code_fence(self):
        text = f"```json\n{json.dumps(MOCK_TIERS)}\n```"
        result = _parse_tiers(text)
        assert result["tier_1"] == MOCK_TIERS["tier_1"]

    def test_returns_empty_tiers_on_no_json(self):
        result = _parse_tiers("Sorry, I cannot help.")
        assert result == {"tier_1": [], "tier_2": [], "tier_3": []}

    def test_returns_empty_tiers_on_malformed_json(self):
        result = _parse_tiers("{not valid json}")
        assert result == {"tier_1": [], "tier_2": [], "tier_3": []}

    def test_missing_tier_keys_default_to_empty_list(self):
        result = _parse_tiers('{"tier_1": ["Lemon juice"]}')
        assert result["tier_2"] == []
        assert result["tier_3"] == []


class TestSuggest:
    def test_creates_chat_with_system_prompt(self, mock_chat):
        suggest(SUGGESTIONS)
        call_kwargs = mock_chat.chats.create.call_args[1]
        system_instruction = call_kwargs["config"].system_instruction
        assert system_instruction == shopper_module.SYSTEM_PROMPT

    def test_message_contains_missing_ingredients(self, mock_chat):
        suggest(SUGGESTIONS)
        message = mock_chat.chats.create.return_value.send_message.call_args[0][0]
        assert "Simple syrup" in message
        assert "Absinthe" in message

    def test_message_excludes_pantry_ingredients(self, mock_chat):
        suggest(SUGGESTIONS)
        message = mock_chat.chats.create.return_value.send_message.call_args[0][0]
        assert "White rum" not in message
        assert "Gin" not in message

    def test_returns_dict_with_required_keys(self, mock_chat):
        result = suggest(SUGGESTIONS)
        assert "tier_1" in result
        assert "tier_2" in result
        assert "tier_3" in result
        assert "stock_up" in result

    def test_stock_up_sorted_by_recipes_unlocked_descending(self, mock_chat):
        result = suggest(SUGGESTIONS)
        counts = [item["recipes_unlocked"] for item in result["stock_up"]]
        assert counts == sorted(counts, reverse=True)

    def test_stock_up_contains_only_tier_1_items(self, mock_chat):
        result = suggest(SUGGESTIONS)
        stock_up_names = {item["name"] for item in result["stock_up"]}
        assert stock_up_names <= set(result["tier_1"])

    def test_stock_up_recipes_unlocked_reflects_counts(self, mock_chat):
        result = suggest(SUGGESTIONS)
        simple_syrup = next(
            item for item in result["stock_up"] if item["name"] == "Simple syrup"
        )
        assert simple_syrup["recipes_unlocked"] == 2

    def test_no_missing_ingredients_skips_gemini(self, mock_chat):
        all_in_pantry = [
            {
                "name": "Gin & Tonic",
                "ingredients": [
                    {"name": "Gin", "in_pantry": True},
                    {"name": "Tonic water", "in_pantry": True},
                ],
                "match_score": 1.0,
            }
        ]
        result = suggest(all_in_pantry)
        mock_chat.chats.create.assert_not_called()
        assert result == {"tier_1": [], "tier_2": [], "tier_3": [], "stock_up": []}
