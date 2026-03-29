# Plan: CC-7

## Work Item
**Title:** Pantry categoriser

## Overview
CC-7 builds the pantry auto-categorisation tool for Cocktail Cabinet, allowing users to dump ingredients into Pantry.md unstructured and have Gemini organise them. A `categorise_pantry()` function sends a flat ingredient list to Gemini and returns a structured dict of categories. `read_pantry()` is updated to detect uncategorised items and trigger categorisation automatically, rewriting the vault file with the organised result.

## Phases

### Phase 1: Create branch plan
Commit the branch plan so it is tracked in git from the start of the branch.

- [X] Create `.claude/plans/CC-7.md`

**Commit message:**
```
docs: add branch plan for CC-7

Documents the implementation phases for the pantry categoriser tool,
including the Gemini prompt call, declaration registration, and
read_pantry integration.

[CC-7]
```

### Phase 2: Categoriser function
Build `categorise_pantry()` in its own module — a focused Gemini prompt call that takes a flat ingredient list and returns a structured dict. Committed independently before it is wired into the vault reader.

- [ ] Write `src/tools/categoriser.py` with `categorise_pantry(items: list[str]) -> dict[str, list[str]]` — builds a prompt, calls `generate()` from `gemini_client`, parses the JSON response into the expected category structure (spirits, liqueurs, mixers, juices, syrups, bitters, garnishes, other)
- [ ] Add module and function docstrings

**Commit message:**
```
feat: add pantry categoriser using Gemini prompt call

categorise_pantry() sends a flat ingredient list to Gemini and returns
a structured dict of categories, enabling unstructured pantry input.

[CC-7]
```

### Phase 3: Declaration and vault reader integration
Register `categorise_pantry` as a Gemini FunctionDeclaration and update `read_pantry()` to auto-categorise and rewrite Pantry.md when an uncategorised section is detected.

- [ ] Add `categorise_pantry_declaration` to `src/tools/declarations.py` and include it in `VAULT_TOOLS`
- [ ] Update `read_pantry()` in `vault_reader.py` to detect an `## Uncategorised` section, call `categorise_pantry()` with those items, merge the result with existing categories, and rewrite Pantry.md

**Commit message:**
```
feat: integrate categoriser into read_pantry and register declaration

read_pantry() now auto-categorises items in an Uncategorised section
and rewrites Pantry.md. Adds categorise_pantry FunctionDeclaration
to VAULT_TOOLS.

[CC-7]
```

### Phase 4: Tests
Write tests for the categoriser and the updated read_pantry behaviour, using mocks to avoid live Gemini calls in unit tests.

- [ ] Write `tests/test_categoriser.py` — unit test mocking `generate()` to assert `categorise_pantry()` sends a prompt containing the ingredients and correctly parses the response into a category dict
- [ ] Update `tests/test_vault_reader.py` — add a test that provides a Pantry.md with an `## Uncategorised` section and asserts `read_pantry()` calls `categorise_pantry()` and rewrites the file
- [ ] Update `tests/test_declarations.py` — assert `VAULT_TOOLS` now contains six declarations

**Commit message:**
```
test: add tests for categoriser and updated read_pantry behaviour

Unit tests mock the Gemini call to verify categorisation logic.
read_pantry tests cover auto-categorisation trigger and file rewrite.

[CC-7]
```
