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


@pytest.fixture(autouse=True)
def mock_pipeline(mocker):
    """Mock orchestrator and vault writer for all tests."""
    mocker.patch("src.orchestrator.run", return_value=MOCK_MARKDOWN)
    mocker.patch("src.orchestrator.update_preferences", return_value=MOCK_PREFERENCE_SUMMARY)
    mocker.patch("src.tools.vault_writer.write_suggestion", return_value=MOCK_CONFIRMATION)


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
