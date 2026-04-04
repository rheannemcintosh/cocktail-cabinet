"""
Tests for the prompt orchestration chain.

Mocks vault readers, mood mapping, and the bartender agent to verify
each step executes in order and passes its output into the next.
"""
import pytest

import src.orchestrator as orchestrator_module
from src.orchestrator import run, update_preferences

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
MOCK_BOOSTED_SUGGESTIONS = [
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
def mock_taste(mocker):
    """Mock taste.filter_and_boost() to return fixed boosted suggestions."""
    return mocker.patch.object(
        orchestrator_module.taste, "filter_and_boost", return_value=MOCK_BOOSTED_SUGGESTIONS
    )


@pytest.fixture
def mock_shopper(mocker):
    """Mock shopper.suggest() to return a fixed shopping dict."""
    return mocker.patch.object(
        orchestrator_module.shopper, "suggest", return_value=MOCK_SHOPPING
    )


class TestRun:
    def test_calls_read_pantry(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        run("refreshing")
        orchestrator_module.read_pantry.assert_called_once()

    def test_calls_read_preferences(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        run("refreshing")
        orchestrator_module.read_preferences.assert_called_once()

    def test_calls_read_cocktail_log(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        run("refreshing")
        orchestrator_module.read_cocktail_log.assert_called_once()

    def test_calls_map_mood_to_flavour_with_mood(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        run("refreshing")
        orchestrator_module.map_mood_to_flavour.assert_called_once_with("refreshing")

    def test_calls_bartender_with_pantry_and_flavour_profile(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        run("refreshing")
        orchestrator_module.bartender.suggest.assert_called_once_with(
            MOCK_PANTRY, MOCK_FLAVOUR_PROFILE
        )

    def test_calls_taste_with_suggestions_preferences_and_log(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        run("refreshing")
        orchestrator_module.taste.filter_and_boost.assert_called_once_with(
            MOCK_SUGGESTIONS, MOCK_PREFERENCES, MOCK_LOG
        )

    def test_calls_shopper_with_taste_output(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        run("refreshing")
        orchestrator_module.shopper.suggest.assert_called_once_with(MOCK_BOOSTED_SUGGESTIONS)

    def test_output_contains_cocktail_name(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        result = run("refreshing")
        assert "Gin & Tonic" in result

    def test_output_contains_mood(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        result = run("refreshing")
        assert "refreshing" in result

    def test_output_contains_shopping_list(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        result = run("refreshing")
        assert "Shopping list" in result
        assert "Lemon juice" in result

    def test_output_is_markdown_string(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper):
        result = run("refreshing")
        assert isinstance(result, str)
        assert result.startswith("# Cocktail Suggestions")


class TestRunProgressLogging:
    def test_prints_pantry_step(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing")
        assert "Browsing what's in the pantry" in capsys.readouterr().out

    def test_prints_preferences_step(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing")
        assert "Reminding myself what you like" in capsys.readouterr().out

    def test_prints_cocktail_log_step(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing")
        assert "Looking at what we've made before" in capsys.readouterr().out

    def test_prints_mood_step(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing")
        assert "Getting a feel for your mood" in capsys.readouterr().out

    def test_prints_bartender_step(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing")
        assert "Asking the bartender what they'd recommend" in capsys.readouterr().out

    def test_prints_taste_step(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing")
        assert "Making sure you'll actually enjoy it" in capsys.readouterr().out

    def test_prints_shopper_step(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing")
        assert "Checking what you might need to pick up" in capsys.readouterr().out


class TestVerboseMode:
    def test_verbose_prints_mood(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing", verbose=True)
        assert "refreshing" in capsys.readouterr().out

    def test_verbose_prints_flavour_notes(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing", verbose=True)
        assert "citrus" in capsys.readouterr().out

    def test_verbose_prints_suggestion_count(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing", verbose=True)
        assert "bartender returned" in capsys.readouterr().out

    def test_verbose_prints_filtered_count(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing", verbose=True)
        assert "kept" in capsys.readouterr().out

    def test_verbose_prints_shopping_tiers(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing", verbose=True)
        assert "tier 1" in capsys.readouterr().out

    def test_non_verbose_omits_mood_detail(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing", verbose=False)
        assert "flavour notes" not in capsys.readouterr().out

    def test_non_verbose_omits_suggestion_count(self, mock_vault, mock_mood, mock_bartender, mock_taste, mock_shopper, capsys):
        run("refreshing", verbose=False)
        assert "bartender returned" not in capsys.readouterr().out

    def test_update_preferences_verbose_prints_log_count(self, mock_vault, mocker, capsys):
        mocker.patch.object(orchestrator_module.taste, "infer_and_update", return_value="")
        update_preferences(verbose=True)
        assert "cocktail log entry" in capsys.readouterr().out

    def test_update_preferences_non_verbose_omits_log_count(self, mock_vault, mocker, capsys):
        mocker.patch.object(orchestrator_module.taste, "infer_and_update", return_value="")
        update_preferences(verbose=False)
        assert "cocktail log entry" not in capsys.readouterr().out


class TestUpdatePreferences:
    @pytest.fixture
    def mock_infer(self, mocker):
        return mocker.patch.object(
            orchestrator_module.taste, "infer_and_update", return_value="Preferences updated."
        )

    def test_calls_read_preferences(self, mock_vault, mock_infer):
        update_preferences()
        orchestrator_module.read_preferences.assert_called_once()

    def test_calls_read_cocktail_log(self, mock_vault, mock_infer):
        update_preferences()
        orchestrator_module.read_cocktail_log.assert_called_once()

    def test_calls_infer_and_update_with_log_and_preferences(self, mock_vault, mock_infer):
        update_preferences()
        orchestrator_module.taste.infer_and_update.assert_called_once_with(
            MOCK_LOG, MOCK_PREFERENCES
        )

    def test_returns_summary_from_taste_agent(self, mock_vault, mock_infer):
        result = update_preferences()
        assert result == "Preferences updated."

    def test_prints_preference_update_step(self, mock_vault, mock_infer, capsys):
        update_preferences()
        assert "Learning from what you've rated before" in capsys.readouterr().out
