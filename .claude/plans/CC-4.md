# Plan: CC-4

## Work Item
**Title:** Connect to Gemini API

## Overview
CC-4 wires up the Google Gemini API as the first real integration step for Cocktail Cabinet. A lightweight client wrapper initialises the google-genai SDK and exposes a simple interface for sending prompts, verified with a live call. Unit tests cover the wrapper with mocks, and an integration test confirms the live connection, skipping gracefully if no API key is present.

## Phases

### Phase 1: Create branch plan
Commit the branch plan so it is tracked in git from the start of the branch.

- [X] Create `.claude/plans/CC-4.md`

**Commit message:**
```
docs: add branch plan for CC-4

Documents the implementation phases for connecting to the Gemini API
and writing unit and integration tests.

[CC-4]
```

### Phase 2: Gemini client wrapper
Create a thin wrapper around the google-genai SDK that initialises the client from config and exposes a `generate` function for sending prompts.

- [X] Write `src/gemini_client.py` — initialises `google.genai.Client` with `GEMINI_API_KEY`, exposes `generate(prompt: str) -> str` function, includes module and function docstrings

**Commit message:**
```
feat: add Gemini client wrapper

Thin wrapper around the google-genai SDK that initialises the client
from config and exposes a generate() function for sending prompts.

[CC-4]
```

### Phase 3: Add test dependencies
Add pytest and pytest-mock as dev dependencies via uv so tests can be run before any implementation is committed.

- [X] Run `uv add --dev pytest pytest-mock` to add test dependencies
- [X] Verify `uv run pytest` runs without errors on the empty test suite

**Commit message:**
```
build: add pytest and pytest-mock as dev dependencies

Adds test tooling via uv so the test suite can be run from the start
of the branch.

[CC-4]
```

### Phase 4: Tests
Write unit tests with mocked SDK calls and an integration test that makes a live call and skips if `GEMINI_API_KEY` is not set.

- [ ] Write `tests/test_gemini_client.py` — unit test mocking `google.genai.Client` to verify `generate()` sends the prompt and returns the response text
- [ ] Add an integration test marked with `pytest.mark.skipif` that calls the live API and asserts a non-empty string response

**Commit message:**
```
test: add unit and integration tests for Gemini client

Unit test mocks the SDK to verify prompt handling. Integration test
calls the live API and skips automatically if GEMINI_API_KEY is unset.

[CC-4]
```
