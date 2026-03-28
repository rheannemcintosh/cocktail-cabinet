"""
Tests for the Gemini API client wrapper.

Includes a unit test with a mocked SDK and an integration test that
calls the live API, skipped if GEMINI_API_KEY is not set.
"""
import os
from unittest.mock import MagicMock, patch

import pytest


def test_generate_sends_prompt_and_returns_text(mocker):
    """generate() passes the prompt to the SDK and returns response text."""
    mock_response = MagicMock()
    mock_response.text = "Hello from Gemini!"

    mock_client = MagicMock()
    mock_client.models.generate_content.return_value = mock_response

    mocker.patch("src.gemini_client._client", mock_client)

    from src.gemini_client import MODEL, generate

    result = generate("Say hello")

    mock_client.models.generate_content.assert_called_once_with(
        model=MODEL,
        contents="Say hello",
    )
    assert result == "Hello from Gemini!"


@pytest.mark.skipif(
    os.getenv("GEMINI_API_KEY") in (None, "test-api-key"),
    reason="GEMINI_API_KEY not set — skipping live API call",
)
def test_generate_live_call():
    """generate() returns a non-empty string from the live Gemini API."""
    from src.gemini_client import generate

    result = generate("Reply with one word: hello")

    assert isinstance(result, str)
    assert len(result) > 0
