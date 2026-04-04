"""
Integration tests for the main.py CLI entry point.

Mocks the orchestrator and vault writer at the module boundary to verify
argument parsing, the full call chain, output, and error handling.
"""
import sys

import pytest

from src.main import main

MOCK_MARKDOWN = "# Cocktail Suggestions\n\nGin & Tonic"
MOCK_CONFIRMATION = "Cocktail suggestions written to /fake/vault/Cocktail Suggestions.md"
MOCK_PREFERENCE_SUMMARY = "No new taste patterns inferred — preferences unchanged."
MOCK_SUGGESTIONS = ["Gin & Tonic", "Daiquiri", "Mojito"]
MOCK_LOG_CONFIRMATION = "Entry added to Cocktail Log.md"


@pytest.fixture(autouse=True)
def mock_pipeline(mocker):
    """Mock orchestrator, vault reader, and vault writer for all tests."""
    mocker.patch("src.orchestrator.run", return_value=MOCK_MARKDOWN)
    mocker.patch("src.orchestrator.update_preferences", return_value=MOCK_PREFERENCE_SUMMARY)
    mocker.patch("src.tools.vault_writer.write_suggestion", return_value=MOCK_CONFIRMATION)
    mocker.patch("src.tools.vault_reader.read_suggestions", return_value=[])
    mocker.patch("src.tools.vault_writer.write_to_log", return_value=MOCK_LOG_CONFIRMATION)


class TestMain:
    def test_passes_mood_to_orchestrator(self, mocker):
        mocker.patch("sys.argv", ["main", "--mood", "refreshing"])
        main()
        import src.orchestrator
        src.orchestrator.run.assert_called_once_with("refreshing", verbose=False)

    def test_passes_verbose_true_when_flag_set(self, mocker):
        mocker.patch("sys.argv", ["main", "--mood", "refreshing", "--verbose"])
        main()
        import src.orchestrator
        src.orchestrator.run.assert_called_once_with("refreshing", verbose=True)

    def test_passes_verbose_false_by_default(self, mocker):
        mocker.patch("sys.argv", ["main", "--mood", "refreshing"])
        main()
        import src.orchestrator
        src.orchestrator.run.assert_called_once_with("refreshing", verbose=False)

    def test_passes_run_result_to_write_suggestion(self, mocker):
        mocker.patch("sys.argv", ["main", "--mood", "tropical"])
        main()
        import src.tools.vault_writer
        src.tools.vault_writer.write_suggestion.assert_called_once_with(MOCK_MARKDOWN)

    def test_calls_update_preferences_on_every_run(self, mocker):
        mocker.patch("sys.argv", ["main", "--mood", "cosy"])
        main()
        import src.orchestrator
        src.orchestrator.update_preferences.assert_called_once()

    def test_prints_vault_confirmation(self, mocker, capsys):
        mocker.patch("sys.argv", ["main", "--mood", "refreshing"])
        main()
        assert MOCK_CONFIRMATION in capsys.readouterr().out

    def test_prints_preference_summary(self, mocker, capsys):
        mocker.patch("sys.argv", ["main", "--mood", "refreshing"])
        main()
        assert MOCK_PREFERENCE_SUMMARY in capsys.readouterr().out

    def test_missing_mood_exits_nonzero(self, mocker):
        mocker.patch("sys.argv", ["main"])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    def test_config_error_exits_with_code_1(self, mocker, monkeypatch):
        mocker.patch("sys.argv", ["main", "--mood", "refreshing"])

        class _FailingConfig:
            def __getattr__(self, name):
                raise EnvironmentError(f"Missing required environment variable: {name}")

        monkeypatch.setitem(sys.modules, "src.config", _FailingConfig())
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    def test_config_error_prints_message(self, mocker, monkeypatch, capsys):
        mocker.patch("sys.argv", ["main", "--mood", "refreshing"])

        class _FailingConfig:
            def __getattr__(self, name):
                raise EnvironmentError(f"Missing required environment variable: {name}")

        monkeypatch.setitem(sys.modules, "src.config", _FailingConfig())
        with pytest.raises(SystemExit):
            main()
        assert "Configuration error" in capsys.readouterr().out


class TestPromptToLog:
    @pytest.fixture(autouse=True)
    def with_suggestions(self, mocker):
        mocker.patch("src.tools.vault_reader.read_suggestions", return_value=MOCK_SUGGESTIONS)
        mocker.patch("sys.argv", ["main", "--mood", "refreshing"])

    def test_skip_on_empty_input_does_not_call_write_to_log(self, mocker):
        mocker.patch("builtins.input", return_value="")
        main()
        import src.tools.vault_writer
        src.tools.vault_writer.write_to_log.assert_not_called()

    def test_valid_selection_calls_write_to_log(self, mocker):
        mocker.patch("builtins.input", side_effect=["1", "4", "Delicious"])
        main()
        import src.tools.vault_writer
        src.tools.vault_writer.write_to_log.assert_called_once_with("Gin & Tonic", 4, "Delicious")

    def test_valid_selection_with_empty_notes_passes_empty_string(self, mocker):
        mocker.patch("builtins.input", side_effect=["2", "3", ""])
        main()
        import src.tools.vault_writer
        src.tools.vault_writer.write_to_log.assert_called_once_with("Daiquiri", 3, "")

    def test_out_of_range_selection_does_not_call_write_to_log(self, mocker):
        mocker.patch("builtins.input", return_value="99")
        main()
        import src.tools.vault_writer
        src.tools.vault_writer.write_to_log.assert_not_called()

    def test_non_numeric_selection_does_not_call_write_to_log(self, mocker):
        mocker.patch("builtins.input", return_value="abc")
        main()
        import src.tools.vault_writer
        src.tools.vault_writer.write_to_log.assert_not_called()

    def test_prints_log_confirmation_after_valid_selection(self, mocker, capsys):
        mocker.patch("builtins.input", side_effect=["1", "5", ""])
        main()
        assert MOCK_LOG_CONFIRMATION in capsys.readouterr().out

    def test_no_suggestions_skips_prompt(self, mocker):
        mocker.patch("src.tools.vault_reader.read_suggestions", return_value=[])
        mock_input = mocker.patch("builtins.input")
        main()
        mock_input.assert_not_called()


class TestLogCommand:
    def test_calls_write_to_log_with_correct_args(self, mocker):
        mocker.patch("sys.argv", ["main", "--log", "Daiquiri", "--rating", "4"])
        main()
        import src.tools.vault_writer
        src.tools.vault_writer.write_to_log.assert_called_once_with("Daiquiri", 4, "")

    def test_passes_notes_to_write_to_log(self, mocker):
        mocker.patch("sys.argv", ["main", "--log", "Daiquiri", "--rating", "4", "--notes", "Very smooth"])
        main()
        import src.tools.vault_writer
        src.tools.vault_writer.write_to_log.assert_called_once_with("Daiquiri", 4, "Very smooth")

    def test_does_not_call_orchestrator_run(self, mocker):
        mocker.patch("sys.argv", ["main", "--log", "Daiquiri", "--rating", "4"])
        main()
        import src.orchestrator
        src.orchestrator.run.assert_not_called()

    def test_prints_log_confirmation(self, mocker, capsys):
        mocker.patch("sys.argv", ["main", "--log", "Daiquiri", "--rating", "4"])
        main()
        assert MOCK_LOG_CONFIRMATION in capsys.readouterr().out

    def test_missing_rating_exits_nonzero(self, mocker):
        mocker.patch("sys.argv", ["main", "--log", "Daiquiri"])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0

    def test_neither_mood_nor_log_exits_nonzero(self, mocker):
        mocker.patch("sys.argv", ["main"])
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code != 0
