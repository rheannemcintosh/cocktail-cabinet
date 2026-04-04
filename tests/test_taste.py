"""
Tests for the taste agent.

Mocks the Gemini chat and vault writer to avoid live API calls and file I/O.
Covers preference-based filtering, score boosting, preference inference,
Gemini prompt construction, and parse robustness.
"""
import json
from unittest.mock import MagicMock, patch

import pytest

import src.agents.taste as taste_module
from src.agents.taste import (
    _filter_disliked,
    _parse_boosts,
    _parse_preference_updates,
    filter_and_boost,
    infer_and_update,
)

SUGGESTIONS = [
    {
        "name": "Daiquiri",
        "ingredients": [
            {"name": "White rum", "in_pantry": True},
            {"name": "Lime juice", "in_pantry": True},
            {"name": "Simple syrup", "in_pantry": True},
        ],
        "match_score": 1.0,
    },
    {
        "name": "Negroni",
        "ingredients": [
            {"name": "Gin", "in_pantry": True},
            {"name": "Campari", "in_pantry": True},
            {"name": "Sweet vermouth", "in_pantry": True},
        ],
        "match_score": 1.0,
    },
    {
        "name": "Absinthe Frappe",
        "ingredients": [
            {"name": "Absinthe", "in_pantry": True},
            {"name": "Simple syrup", "in_pantry": True},
        ],
        "match_score": 1.0,
    },
]

PREFERENCES = {
    "I like": ["Citrusy", "Refreshing"],
    "I dislike": ["Absinthe", "Smoky"],
    "Preferred spirits": ["Gin", "Rum"],
    "Preferred style": ["Light and sessionable"],
}

COCKTAIL_LOG = [
    {"date": "2026-03-01", "cocktail": "Gimlet", "rating": "5", "notes": "Crisp and citrusy."},
    {"date": "2026-03-10", "cocktail": "Espresso Martini", "rating": "2", "notes": "Too sweet."},
    {"date": "2026-03-15", "cocktail": "Daiquiri", "rating": "4", "notes": "Simple and perfect."},
]

MOCK_BOOSTS = {"Daiquiri": 0.0, "Negroni": 0.1}


def _make_mock_chat(mocker, response_text):
    """Helper: patch _client and return a mock that responds with response_text."""
    mock_response = MagicMock()
    mock_response.text = response_text

    mock_chat_session = MagicMock()
    mock_chat_session.send_message.return_value = mock_response

    mock_client = MagicMock()
    mock_client.chats.create.return_value = mock_chat_session

    mocker.patch.object(taste_module, "_client", mock_client)
    return mock_client


class TestFilterDisliked:
    def test_removes_suggestions_with_disliked_ingredients(self):
        result = _filter_disliked(SUGGESTIONS, PREFERENCES)
        names = [c["name"] for c in result]
        assert "Absinthe Frappe" not in names

    def test_keeps_suggestions_without_disliked_ingredients(self):
        result = _filter_disliked(SUGGESTIONS, PREFERENCES)
        names = [c["name"] for c in result]
        assert "Daiquiri" in names
        assert "Negroni" in names

    def test_match_is_case_insensitive(self):
        prefs = {"I dislike": ["campari"]}
        result = _filter_disliked(SUGGESTIONS, prefs)
        names = [c["name"] for c in result]
        assert "Negroni" not in names

    def test_empty_dislike_list_returns_all_suggestions(self):
        result = _filter_disliked(SUGGESTIONS, {"I dislike": []})
        assert len(result) == len(SUGGESTIONS)

    def test_no_dislike_key_returns_all_suggestions(self):
        result = _filter_disliked(SUGGESTIONS, {})
        assert len(result) == len(SUGGESTIONS)

    def test_returns_empty_list_when_all_filtered(self):
        prefs = {"I dislike": ["rum", "gin", "absinthe"]}
        result = _filter_disliked(SUGGESTIONS, prefs)
        assert result == []


class TestParseBoosts:
    def test_parses_valid_json_object(self):
        result = _parse_boosts(json.dumps(MOCK_BOOSTS))
        assert result["Daiquiri"] == 0.0
        assert result["Negroni"] == 0.1

    def test_parses_json_in_code_fence(self):
        text = f"```json\n{json.dumps(MOCK_BOOSTS)}\n```"
        result = _parse_boosts(text)
        assert result["Negroni"] == 0.1

    def test_returns_empty_dict_on_no_json(self):
        assert _parse_boosts("Sorry, I cannot help.") == {}

    def test_returns_empty_dict_on_malformed_json(self):
        assert _parse_boosts("{not valid json}") == {}


class TestParsePreferenceUpdates:
    MOCK_UPDATES = {"I like": ["Sour", "Spirit-forward"], "Preferred style": ["Short drinks"]}

    def test_parses_valid_json_object(self):
        result = _parse_preference_updates(json.dumps(self.MOCK_UPDATES))
        assert result["I like"] == ["Sour", "Spirit-forward"]

    def test_parses_json_in_code_fence(self):
        text = f"```json\n{json.dumps(self.MOCK_UPDATES)}\n```"
        result = _parse_preference_updates(text)
        assert "Preferred style" in result

    def test_returns_empty_dict_on_no_json(self):
        assert _parse_preference_updates("No patterns found.") == {}

    def test_returns_empty_dict_on_malformed_json(self):
        assert _parse_preference_updates("{bad}") == {}


class TestFilterAndBoost:
    def test_filters_disliked_before_calling_gemini(self, mocker):
        mock_client = _make_mock_chat(mocker, json.dumps(MOCK_BOOSTS))
        result = filter_and_boost(SUGGESTIONS, PREFERENCES, COCKTAIL_LOG)
        names = [c["name"] for c in result]
        assert "Absinthe Frappe" not in names

    def test_creates_chat_with_boost_system_prompt(self, mocker):
        mock_client = _make_mock_chat(mocker, json.dumps(MOCK_BOOSTS))
        filter_and_boost(SUGGESTIONS, PREFERENCES, COCKTAIL_LOG)
        call_kwargs = mock_client.chats.create.call_args[1]
        assert call_kwargs["config"].system_instruction == taste_module.BOOST_SYSTEM_PROMPT

    def test_message_contains_high_rated_cocktails(self, mocker):
        mock_client = _make_mock_chat(mocker, json.dumps(MOCK_BOOSTS))
        filter_and_boost(SUGGESTIONS, PREFERENCES, COCKTAIL_LOG)
        message = mock_client.chats.create.return_value.send_message.call_args[0][0]
        assert "Gimlet" in message
        assert "Daiquiri" in message

    def test_message_excludes_low_rated_cocktails(self, mocker):
        mock_client = _make_mock_chat(mocker, json.dumps(MOCK_BOOSTS))
        filter_and_boost(SUGGESTIONS, PREFERENCES, COCKTAIL_LOG)
        message = mock_client.chats.create.return_value.send_message.call_args[0][0]
        assert "Espresso Martini" not in message

    def test_boost_is_applied_to_match_score(self, mocker):
        _make_mock_chat(mocker, json.dumps({"Negroni": 0.1}))
        result = filter_and_boost(SUGGESTIONS, PREFERENCES, COCKTAIL_LOG)
        negroni = next(c for c in result if c["name"] == "Negroni")
        assert negroni["match_score"] == pytest.approx(1.0)  # 1.0 + 0.1 capped at 1.0

    def test_boost_does_not_exceed_1_0(self, mocker):
        _make_mock_chat(mocker, json.dumps({"Daiquiri": 0.2, "Negroni": 0.2}))
        result = filter_and_boost(SUGGESTIONS, PREFERENCES, COCKTAIL_LOG)
        for cocktail in result:
            assert cocktail["match_score"] <= 1.0

    def test_result_sorted_by_match_score_descending(self, mocker):
        _make_mock_chat(mocker, json.dumps({"Negroni": 0.15, "Daiquiri": 0.0}))
        result = filter_and_boost(SUGGESTIONS, PREFERENCES, COCKTAIL_LOG)
        scores = [c["match_score"] for c in result]
        assert scores == sorted(scores, reverse=True)

    def test_skips_gemini_when_no_high_rated_log_entries(self, mocker):
        mock_client = _make_mock_chat(mocker, "{}")
        low_rated_log = [
            {"date": "2026-03-01", "cocktail": "Negroni", "rating": "2", "notes": ""},
        ]
        filter_and_boost(SUGGESTIONS, PREFERENCES, low_rated_log)
        mock_client.chats.create.assert_not_called()

    def test_skips_gemini_when_log_is_empty(self, mocker):
        mock_client = _make_mock_chat(mocker, "{}")
        filter_and_boost(SUGGESTIONS, PREFERENCES, [])
        mock_client.chats.create.assert_not_called()

    def test_returns_empty_list_when_all_filtered(self, mocker):
        mock_client = _make_mock_chat(mocker, "{}")
        prefs = {"I dislike": ["rum", "gin", "absinthe"]}
        result = filter_and_boost(SUGGESTIONS, prefs, COCKTAIL_LOG)
        assert result == []
        mock_client.chats.create.assert_not_called()


class TestInferAndUpdate:
    MOCK_UPDATES = {"I like": ["Sour"], "Preferred style": ["Short drinks"]}

    @pytest.fixture
    def mock_write_preferences(self, mocker):
        return mocker.patch.object(taste_module, "write_preferences")

    def test_creates_chat_with_infer_system_prompt(self, mocker, mock_write_preferences):
        mock_client = _make_mock_chat(mocker, json.dumps(self.MOCK_UPDATES))
        infer_and_update(COCKTAIL_LOG, PREFERENCES)
        call_kwargs = mock_client.chats.create.call_args[1]
        assert call_kwargs["config"].system_instruction == taste_module.INFER_SYSTEM_PROMPT

    def test_message_contains_all_log_entries(self, mocker, mock_write_preferences):
        mock_client = _make_mock_chat(mocker, json.dumps(self.MOCK_UPDATES))
        infer_and_update(COCKTAIL_LOG, PREFERENCES)
        message = mock_client.chats.create.return_value.send_message.call_args[0][0]
        assert "Gimlet" in message
        assert "Espresso Martini" in message
        assert "Daiquiri" in message

    def test_message_contains_current_preferences(self, mocker, mock_write_preferences):
        mock_client = _make_mock_chat(mocker, json.dumps(self.MOCK_UPDATES))
        infer_and_update(COCKTAIL_LOG, PREFERENCES)
        message = mock_client.chats.create.return_value.send_message.call_args[0][0]
        assert "Citrusy" in message

    def test_merges_new_items_into_existing_preferences(self, mocker, mock_write_preferences):
        _make_mock_chat(mocker, json.dumps(self.MOCK_UPDATES))
        infer_and_update(COCKTAIL_LOG, PREFERENCES)
        written = mock_write_preferences.call_args[0][0]
        assert "Sour" in written["I like"]
        assert "Citrusy" in written["I like"]

    def test_does_not_duplicate_existing_preferences(self, mocker, mock_write_preferences):
        updates_with_duplicate = {"I like": ["Citrusy", "Sour"]}
        _make_mock_chat(mocker, json.dumps(updates_with_duplicate))
        infer_and_update(COCKTAIL_LOG, PREFERENCES)
        written = mock_write_preferences.call_args[0][0]
        assert written["I like"].count("Citrusy") == 1

    def test_deduplication_is_case_insensitive(self, mocker, mock_write_preferences):
        updates_with_case_variant = {"I like": ["citrusy", "Sour"]}
        _make_mock_chat(mocker, json.dumps(updates_with_case_variant))
        infer_and_update(COCKTAIL_LOG, PREFERENCES)
        written = mock_write_preferences.call_args[0][0]
        citrusy_count = sum(1 for item in written["I like"] if item.lower() == "citrusy")
        assert citrusy_count == 1

    def test_skips_gemini_when_log_is_empty(self, mocker, mock_write_preferences):
        mock_client = _make_mock_chat(mocker, "{}")
        result = infer_and_update([], PREFERENCES)
        mock_client.chats.create.assert_not_called()
        mock_write_preferences.assert_not_called()
        assert "unchanged" in result

    def test_returns_summary_of_added_items(self, mocker, mock_write_preferences):
        _make_mock_chat(mocker, json.dumps(self.MOCK_UPDATES))
        result = infer_and_update(COCKTAIL_LOG, PREFERENCES)
        assert "Sour" in result
        assert "updated" in result.lower()

    def test_returns_unchanged_message_when_no_new_inferences(self, mocker, mock_write_preferences):
        existing_only = {"I like": ["Citrusy", "Refreshing"]}
        _make_mock_chat(mocker, json.dumps(existing_only))
        result = infer_and_update(COCKTAIL_LOG, PREFERENCES)
        assert "unchanged" in result

    def test_returns_unchanged_message_on_unparseable_response(self, mocker, mock_write_preferences):
        _make_mock_chat(mocker, "I cannot determine any patterns.")
        result = infer_and_update(COCKTAIL_LOG, PREFERENCES)
        mock_write_preferences.assert_not_called()
        assert "unchanged" in result
