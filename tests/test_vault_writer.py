"""
Tests for vault writer functions.

Uses tmp_path to write files in isolation so the real vault and
vault_templates/ are never modified by the test suite.
"""
import pytest

import src.tools.vault_writer as vault_writer


@pytest.fixture(autouse=True)
def use_tmp_vault(tmp_path, monkeypatch):
    """Point the vault path at a temporary directory for all tests."""
    monkeypatch.setattr(vault_writer, "OBSIDIAN_VAULT_PATH", str(tmp_path))
    return tmp_path


class TestWriteSuggestion:
    def test_creates_file(self, tmp_path):
        vault_writer.write_suggestion("# Cocktail Suggestions\n\nTest content.")
        assert (tmp_path / "Cocktail Suggestions.md").exists()

    def test_writes_content(self, tmp_path):
        content = "# Cocktail Suggestions\n\nDaiquiri recipe here."
        vault_writer.write_suggestion(content)
        assert (tmp_path / "Cocktail Suggestions.md").read_text() == content

    def test_overwrites_existing_file(self, tmp_path):
        vault_writer.write_suggestion("first content")
        vault_writer.write_suggestion("second content")
        assert (tmp_path / "Cocktail Suggestions.md").read_text() == "second content"

    def test_returns_confirmation_message(self):
        result = vault_writer.write_suggestion("content")
        assert "Cocktail Suggestions" in result


class TestWriteToLog:
    @pytest.fixture(autouse=True)
    def create_log_file(self, tmp_path):
        """Create a minimal Cocktail Log.md before each test."""
        (tmp_path / "Cocktail Log.md").write_text(
            "# Cocktail Log\n\n## Log\n", encoding="utf-8"
        )

    def test_appends_entry_to_log(self, tmp_path):
        vault_writer.write_to_log("Negroni", 4)
        content = (tmp_path / "Cocktail Log.md").read_text()
        assert "Negroni" in content

    def test_entry_contains_rating_stars(self, tmp_path):
        vault_writer.write_to_log("Daiquiri", 5)
        content = (tmp_path / "Cocktail Log.md").read_text()
        assert "⭐⭐⭐⭐⭐" in content

    def test_entry_contains_notes(self, tmp_path):
        vault_writer.write_to_log("Mojito", 3, notes="Needs more lime.")
        content = (tmp_path / "Cocktail Log.md").read_text()
        assert "Needs more lime." in content

    def test_entry_contains_today_date(self, tmp_path):
        from datetime import date
        vault_writer.write_to_log("Margarita", 4)
        content = (tmp_path / "Cocktail Log.md").read_text()
        assert date.today().isoformat() in content

    def test_returns_confirmation_message(self):
        result = vault_writer.write_to_log("Gimlet", 3)
        assert "Gimlet" in result

    def test_invalid_rating_raises_value_error(self):
        with pytest.raises(ValueError):
            vault_writer.write_to_log("Sour", 6)

    def test_missing_log_file_raises_file_not_found(self, tmp_path):
        (tmp_path / "Cocktail Log.md").unlink()
        with pytest.raises(FileNotFoundError):
            vault_writer.write_to_log("Sour", 4)
