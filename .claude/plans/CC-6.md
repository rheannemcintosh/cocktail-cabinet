# Plan: CC-6

## Work Item
**Title:** Vault writer tools

## Overview
CC-6 builds the output side of the tool calling layer for Cocktail Cabinet, completing the vault I/O pattern established in CC-5. Two writer functions handle writing formatted cocktail suggestions to the vault and appending rated entries to the cocktail log. Both are registered as Gemini function declarations so the LLM can call them to persist its output.

## Phases

### Phase 1: Create branch plan
Commit the branch plan so it is tracked in git from the start of the branch.

- [X] Create `.claude/plans/CC-6.md`

**Commit message:**
```
docs: add branch plan for CC-6

Documents the implementation phases for the vault writer tool
functions and their Gemini function declarations.

[CC-6]
```

### Phase 2: Vault writer functions
Build the two Python functions that write output back to the Obsidian vault. This is pure file I/O with no Gemini dependency, committed independently before the declarations.

- [X] Write `src/tools/vault_writer.py` with `write_suggestion(content: str)` — overwrites `Cocktail Suggestions.md` with formatted markdown including recipe, missing ingredients with accessibility tiers, and a rating prompt
- [X] Write `write_to_log(cocktail: str, rating: int, notes: str = "")` — appends a dated entry to `Cocktail Log.md`
- [X] Add module and function docstrings

**Commit message:**
```
feat: add vault writer functions for suggestions and log

write_suggestion() overwrites Cocktail Suggestions.md with a formatted
recipe and shopping tier output. write_to_log() appends a rated entry
to Cocktail Log.md.

[CC-6]
```

### Phase 3: Gemini function declarations
Register both writer functions as Gemini FunctionDeclarations and add them to the existing VAULT_READER_TOOL in declarations.py, so all vault tools are available in a single Tool object.

- [ ] Add `write_suggestion_declaration` and `write_to_log_declaration` to `src/tools/declarations.py` using `FunctionDeclaration.from_callable()`
- [ ] Combine all five declarations into a single `VAULT_TOOLS` list, replacing the existing `VAULT_READER_TOOL`
- [ ] Update the module docstring to reflect the expanded tool set

**Commit message:**
```
feat: add Gemini function declarations for vault writer tools

Registers write_suggestion and write_to_log as FunctionDeclarations
and consolidates all vault tools into a single VAULT_TOOLS export.

[CC-6]
```

### Phase 4: Tests
Write tests for the writer functions and updated declarations.

- [ ] Write `tests/test_vault_writer.py` — tests for `write_suggestion()` asserting the file is created with correct content, and `write_to_log()` asserting the entry is appended with correct date, cocktail, rating, and notes
- [ ] Update `tests/test_declarations.py` to assert `VAULT_TOOLS` now contains five declarations with the correct names

**Commit message:**
```
test: add tests for vault writer functions and updated declarations

Tests cover file creation and content for write_suggestion, log
appending for write_to_log, and the updated five-declaration VAULT_TOOLS
structure.

[CC-6]
```
