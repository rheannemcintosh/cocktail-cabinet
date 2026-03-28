"""
Tests for vault reader functions.

Uses vault_templates/ as fixture data so tests run without a real
Obsidian vault configured.
"""
import pytest

import src.tools.vault_reader as vault_reader


@pytest.fixture(autouse=True)
def use_vault_templates(monkeypatch):
    """Point the vault path at vault_templates/ for all tests in this module."""
    monkeypatch.setattr(vault_reader, "OBSIDIAN_VAULT_PATH", "vault_templates")


class TestReadPantry:
    def test_returns_dict_of_categories(self):
        result = vault_reader.read_pantry()
        assert isinstance(result, dict)

    def test_contains_expected_categories(self):
        result = vault_reader.read_pantry()
        assert "Spirits" in result
        assert "Mixers" in result
        assert "Bitters" in result

    def test_categories_contain_ingredients(self):
        result = vault_reader.read_pantry()
        assert len(result["Spirits"]) > 0
        assert "Gin" in result["Spirits"]

    def test_missing_file_raises_file_not_found(self, monkeypatch):
        monkeypatch.setattr(vault_reader, "OBSIDIAN_VAULT_PATH", "/nonexistent")
        with pytest.raises(FileNotFoundError):
            vault_reader.read_pantry()


class TestReadPreferences:
    def test_returns_dict_of_sections(self):
        result = vault_reader.read_preferences()
        assert isinstance(result, dict)

    def test_contains_likes_and_dislikes(self):
        result = vault_reader.read_preferences()
        assert "I like" in result
        assert "I dislike" in result

    def test_likes_are_non_empty(self):
        result = vault_reader.read_preferences()
        assert len(result["I like"]) > 0

    def test_missing_file_raises_file_not_found(self, monkeypatch):
        monkeypatch.setattr(vault_reader, "OBSIDIAN_VAULT_PATH", "/nonexistent")
        with pytest.raises(FileNotFoundError):
            vault_reader.read_preferences()


class TestReadCocktailLog:
    def test_returns_list_of_entries(self):
        result = vault_reader.read_cocktail_log()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_entries_have_required_keys(self):
        result = vault_reader.read_cocktail_log()
        for entry in result:
            assert "date" in entry
            assert "cocktail" in entry
            assert "rating" in entry
            assert "notes" in entry

    def test_rating_is_numeric_string(self):
        result = vault_reader.read_cocktail_log()
        for entry in result:
            assert entry["rating"].isdigit()

    def test_missing_file_raises_file_not_found(self, monkeypatch):
        monkeypatch.setattr(vault_reader, "OBSIDIAN_VAULT_PATH", "/nonexistent")
        with pytest.raises(FileNotFoundError):
            vault_reader.read_cocktail_log()
