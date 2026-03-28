# Plan: CC-5

## Work Item
**Title:** Vault reader tools

## Overview
CC-5 builds the tool calling layer for Cocktail Cabinet — the first of three LLM integration patterns in the portfolio. Three Python functions parse the Obsidian vault markdown files (pantry, preferences, cocktail log) into structured data, and each is registered as a Gemini function declaration so the LLM can invoke them during a conversation. Tests cover both the parsing logic and the function declaration structure.

## Phases

### Phase 1: Create branch plan
Commit the branch plan so it is tracked in git from the start of the branch.

- [X] Create `.claude/plans/CC-5.md`

**Commit message:**
```
docs: add branch plan for CC-5

Documents the implementation phases for the vault reader tool
functions and their Gemini function declarations.

[CC-5]
```

### Phase 2: Vault reader functions
Build the three Python functions that read and parse the Obsidian vault markdown files into structured data. This is pure parsing logic with no Gemini dependency, so it can be tested and committed independently.

- [X] Write `src/tools/vault_reader.py` with `read_pantry()`, `read_preferences()`, and `read_cocktail_log()` — each reads from `OBSIDIAN_VAULT_PATH`, parses the markdown, and returns a typed dict
- [X] Add module and function docstrings to all functions

**Commit message:**
```
feat: add vault reader functions for pantry, preferences and log

Parses Pantry.md into categorised ingredients, Preferences.md into
likes/dislikes lists, and Cocktail Log.md into rated cocktail entries.

[CC-5]
```

### Phase 3: Gemini function declarations
Define each vault reader as a Gemini function declaration so the LLM can call them as tools during a conversation. Register all three as a tools list ready to be passed to `generate_content`.

- [X] Write `src/tools/declarations.py` — defines a `FunctionDeclaration` for each vault reader function and exports a `VAULT_READER_TOOLS` list
- [X] Add module docstring explaining the tool calling pattern

**Commit message:**
```
feat: add Gemini function declarations for vault reader tools

Defines FunctionDeclarations for read_pantry, read_preferences, and
read_cocktail_log and exports them as a tools list for use in
generate_content calls.

[CC-5]
```

### Phase 4: Tests
Write tests for the parsing logic and the function declaration structure.

- [X] Write `tests/test_vault_reader.py` — unit tests for each reader function using fixture markdown files, asserting correct structure and values are returned
- [X] Write `tests/test_declarations.py` — asserts that `VAULT_READER_TOOLS` contains the correct number of declarations and that each has a name and description

**Commit message:**
```
test: add tests for vault reader functions and declarations

Unit tests cover markdown parsing for all three vault files and assert
that function declarations are correctly structured for Gemini tool use.

[CC-5]
```
