# Plan: CC-8

## Work Item
**Title:** Prompt orchestration chain

## Overview
CC-8 builds the core prompt orchestration chain for Cocktail Cabinet — the pattern that ties the whole tool together. `src/orchestrator.py` implements a four-step chain where each step's output feeds into the next: vault reading, mood-to-flavour mapping, context assembly, and recipe generation. Once complete, `main.py` is wired up to call it so the CLI produces real cocktail suggestions end-to-end.

## Phases

### Phase 1: Create branch plan
Commit the branch plan so it is tracked in git from the start of the branch.

- [X] Create `.claude/plans/CC-8.md`

**Commit message:**
```
docs: add branch plan for CC-8

Documents the implementation phases for the prompt orchestration
chain, mood-to-flavour mapping, context assembly, and CLI wiring.

[CC-8]
```

### Phase 2: Mood-to-flavour mapping
Build the first Gemini prompt in the chain — a focused step that maps a free-text mood to a structured flavour profile. Committed independently so it can be tested in isolation before the full chain is assembled.

- [X] Write `src/mood.py` with `map_mood_to_flavour(mood: str) -> dict` — sends a prompt to Gemini asking it to return a JSON flavour profile (e.g. preferred spirit types, flavour notes, style) for the given mood
- [X] Add module and function docstrings

**Commit message:**
```
feat: add mood-to-flavour mapping prompt

map_mood_to_flavour() sends a mood string to Gemini and returns a
structured flavour profile to use as context in recipe generation.

[CC-8]
```

### Phase 3: Orchestrator
Build `src/orchestrator.py` with a `run(mood: str) -> str` function that executes the full four-step chain. Each step's output is passed into the next as context.

- [X] Write `src/orchestrator.py` with `run(mood: str) -> str`:
  - Step 1: Call `read_pantry()`, `read_preferences()`, `read_cocktail_log()`
  - Step 2: Call `map_mood_to_flavour(mood)` to get flavour profile
  - Step 3: Assemble a structured context string from pantry, preferences, log, and flavour profile
  - Step 4: Send context to Gemini with a recipe generation prompt, return the response
- [X] Add module and function docstrings

**Commit message:**
```
feat: add prompt orchestration chain

Orchestrator runs a four-step chain — vault reading, mood mapping,
context assembly, and recipe generation — returning suggestion text
ready to be written to the vault.

[CC-8]
```

### Phase 4: Wire up CLI and tests
Connect the orchestrator to `main.py` so the CLI produces real output, and write tests covering the chain logic with mocked Gemini calls.

- [X] Update `src/main.py` to call `orchestrator.run(args.mood)` and print the result
- [X] Write `tests/test_mood.py` — unit test mocking `generate()` to assert the prompt contains the mood and the response is parsed into a dict
- [X] Write `tests/test_orchestrator.py` — unit tests mocking vault readers and `generate()` to assert the chain calls each step in order and passes output into context

**Commit message:**
```
feat: wire orchestrator to CLI and add tests

main.py now calls orchestrator.run() to produce real suggestions.
Unit tests mock vault readers and Gemini calls to verify the chain
executes in the correct order with correct context passing.

[CC-8]
```
