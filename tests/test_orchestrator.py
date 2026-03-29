"""
Tests for the prompt orchestration chain.

Mocks vault readers and Gemini calls to verify each step executes in
order and passes its output into the next step's context.
"""
import pytest

import src.orchestrator as orchestrator_module
from src.orchestrator import run


@pytest.fixture
def mock_vault(mocker):
    """Mock all three vault reader functions."""
    mocker.patch.object(
        orchestrator_module,
        "read_pantry",
        return_value={"Spirits": ["Gin"], "Mixers": ["Tonic water"]},
    )
    mocker.patch.object(
        orchestrator_module,
        "read_preferences",
        return_value={"I like": ["Citrusy"], "I dislike": ["Smoky"]},
    )
    mocker.patch.object(
        orchestrator_module,
        "read_cocktail_log",
        return_value=[{"date": "2026-03-01", "cocktail": "Daiquiri", "rating": "5", "notes": "Perfect."}],
    )


@pytest.fixture
def mock_mood(mocker):
    """Mock map_mood_to_flavour to return a fixed flavour profile."""
    return mocker.patch.object(
        orchestrator_module,
        "map_mood_to_flavour",
        return_value={
            "flavour_notes": ["citrus", "light"],
            "preferred_spirits": ["gin"],
            "style": "long",
            "avoid": ["smoky"],
        },
    )


@pytest.fixture
def mock_generate(mocker):
    """Mock the final Gemini generate() call."""
    return mocker.patch.object(
        orchestrator_module,
        "generate",
        return_value="# Cocktail Suggestions\n\nGin & Tonic — you have everything.",
    )


class TestRun:
    def test_calls_read_pantry(self, mock_vault, mock_mood, mock_generate):
        run("refreshing")
        orchestrator_module.read_pantry.assert_called_once()

    def test_calls_read_preferences(self, mock_vault, mock_mood, mock_generate):
        run("refreshing")
        orchestrator_module.read_preferences.assert_called_once()

    def test_calls_read_cocktail_log(self, mock_vault, mock_mood, mock_generate):
        run("refreshing")
        orchestrator_module.read_cocktail_log.assert_called_once()

    def test_calls_map_mood_to_flavour_with_mood(self, mock_vault, mock_mood, mock_generate):
        run("refreshing")
        orchestrator_module.map_mood_to_flavour.assert_called_once_with("refreshing")

    def test_prompt_contains_pantry_context(self, mock_vault, mock_mood, mock_generate):
        run("refreshing")
        prompt = mock_generate.call_args[0][0]
        assert "Gin" in prompt

    def test_prompt_contains_preferences_context(self, mock_vault, mock_mood, mock_generate):
        run("refreshing")
        prompt = mock_generate.call_args[0][0]
        assert "Citrusy" in prompt

    def test_prompt_contains_cocktail_log_context(self, mock_vault, mock_mood, mock_generate):
        run("refreshing")
        prompt = mock_generate.call_args[0][0]
        assert "Daiquiri" in prompt

    def test_prompt_contains_mood(self, mock_vault, mock_mood, mock_generate):
        run("refreshing")
        prompt = mock_generate.call_args[0][0]
        assert "refreshing" in prompt

    def test_returns_generate_output(self, mock_vault, mock_mood, mock_generate):
        result = run("refreshing")
        assert result == "# Cocktail Suggestions\n\nGin & Tonic — you have everything."
