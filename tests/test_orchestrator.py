"""
Tests for the prompt orchestration chain.

Mocks vault readers, mood mapping, and the bartender agent to verify
each step executes in order and passes its output into the next.
"""
import pytest

import src.orchestrator as orchestrator_module
from src.orchestrator import run

MOCK_PANTRY = {"Spirits": ["Gin"], "Mixers": ["Tonic water"]}
MOCK_PREFERENCES = {"I like": ["Citrusy"], "I dislike": ["Smoky"]}
MOCK_LOG = [{"date": "2026-03-01", "cocktail": "Daiquiri", "rating": "5", "notes": "Perfect."}]
MOCK_FLAVOUR_PROFILE = {
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
    }
]
MOCK_SHOPPING = {
    "tier_1": ["Lemon juice"],
    "tier_2": [],
    "tier_3": [],
    "stock_up": [{"name": "Lemon juice", "recipes_unlocked": 1}],
}


@pytest.fixture
def mock_vault(mocker):
    """Mock all three vault reader functions."""
    mocker.patch.object(orchestrator_module, "read_pantry", return_value=MOCK_PANTRY)
    mocker.patch.object(orchestrator_module, "read_preferences", return_value=MOCK_PREFERENCES)
    mocker.patch.object(orchestrator_module, "read_cocktail_log", return_value=MOCK_LOG)


@pytest.fixture
def mock_mood(mocker):
    """Mock map_mood_to_flavour to return a fixed flavour profile."""
    return mocker.patch.object(
        orchestrator_module, "map_mood_to_flavour", return_value=MOCK_FLAVOUR_PROFILE
    )


@pytest.fixture
def mock_bartender(mocker):
    """Mock bartender.suggest() to return fixed suggestions."""
    return mocker.patch.object(
        orchestrator_module.bartender, "suggest", return_value=MOCK_SUGGESTIONS
    )


@pytest.fixture
def mock_shopper(mocker):
    """Mock shopper.suggest() to return a fixed shopping dict."""
    return mocker.patch.object(
        orchestrator_module.shopper, "suggest", return_value=MOCK_SHOPPING
    )


class TestRun:
    def test_calls_read_pantry(self, mock_vault, mock_mood, mock_bartender, mock_shopper):
        run("refreshing")
        orchestrator_module.read_pantry.assert_called_once()

    def test_calls_read_preferences(self, mock_vault, mock_mood, mock_bartender, mock_shopper):
        run("refreshing")
        orchestrator_module.read_preferences.assert_called_once()

    def test_calls_read_cocktail_log(self, mock_vault, mock_mood, mock_bartender, mock_shopper):
        run("refreshing")
        orchestrator_module.read_cocktail_log.assert_called_once()

    def test_calls_map_mood_to_flavour_with_mood(self, mock_vault, mock_mood, mock_bartender, mock_shopper):
        run("refreshing")
        orchestrator_module.map_mood_to_flavour.assert_called_once_with("refreshing")

    def test_calls_bartender_with_pantry_and_flavour_profile(self, mock_vault, mock_mood, mock_bartender, mock_shopper):
        run("refreshing")
        orchestrator_module.bartender.suggest.assert_called_once_with(
            MOCK_PANTRY, MOCK_FLAVOUR_PROFILE
        )

    def test_calls_shopper_with_bartender_suggestions(self, mock_vault, mock_mood, mock_bartender, mock_shopper):
        run("refreshing")
        orchestrator_module.shopper.suggest.assert_called_once_with(MOCK_SUGGESTIONS)

    def test_output_contains_cocktail_name(self, mock_vault, mock_mood, mock_bartender, mock_shopper):
        result = run("refreshing")
        assert "Gin & Tonic" in result

    def test_output_contains_mood(self, mock_vault, mock_mood, mock_bartender, mock_shopper):
        result = run("refreshing")
        assert "refreshing" in result

    def test_output_contains_shopping_list(self, mock_vault, mock_mood, mock_bartender, mock_shopper):
        result = run("refreshing")
        assert "Shopping list" in result
        assert "Lemon juice" in result

    def test_output_is_markdown_string(self, mock_vault, mock_mood, mock_bartender, mock_shopper):
        result = run("refreshing")
        assert isinstance(result, str)
        assert result.startswith("# Cocktail Suggestions")
