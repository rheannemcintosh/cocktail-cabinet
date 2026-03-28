# Plan: CC-2

## Work Item
**Title:** Repository setup — Python CLI with Obsidian integration

## Overview
CC-2 establishes the foundational structure for Cocktail-Cabinet, a Python CLI tool that suggests cocktails based on pantry inventory, mood, and taste preferences. This branch sets up the base Python project using uv, configuration layer, CLI entry point, and Obsidian vault template files — enough to run the tool locally and drop the vault files into Obsidian, but leaving agents and tool-calling modules to their own work items.

## Phases

### Phase 1: Create branch plan
Commit the branch plan so it is tracked in git from the start of the branch.

- [X] Create `.claude/plans/CC-2.md` with phases.

**Commit message:**
```
docs: add branch plan for CC-2

Documents the implementation phases for the repository setup, covering
project scaffold, config and CLI entry point, and vault templates.

[CC-2]
```

### Phase 2: Project scaffold and tooling
Initialise the project with uv so dependencies, Python version, and virtual environment are all managed in one place.

- [ ] Run `uv init` to generate `pyproject.toml` and `.python-version`
- [ ] Run `uv add google-genai python-dotenv` to add dependencies, generate `uv.lock`, and create `.venv`
- [ ] Create `src/__init__.py`
- [ ] Create `tests/` directory with a `.gitkeep` placeholder
- [ ] Write `.env.example` with `GEMINI_API_KEY` and `OBSIDIAN_VAULT_PATH` placeholders
- [ ] Ensure `.gitignore` covers `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `.DS_Store`

**Commit message:**
```
build: initialise project with uv and add dependencies

Sets up the project using uv with google-genai and python-dotenv.
Includes src package, tests directory, .env.example, and .gitignore.

[CC-2]
```

### Phase 3: Config and CLI entry point
Stand up the configuration layer and a working CLI so `uv run python -m src.main --mood "refreshing"` runs end-to-end.

- [ ] Write `src/config.py` — loads `GEMINI_API_KEY` and `OBSIDIAN_VAULT_PATH` from env, exposes typed constants, raises clear errors if required vars are missing
- [ ] Write `src/main.py` — parses `--mood` CLI argument, initialises config, prints a placeholder response to stdout

**Commit message:**
```
feat: add config layer and CLI entry point

Config loads required env vars with clear error messages. CLI parses
--mood argument and prints a placeholder response.

[CC-2]
```

### Phase 4: Vault templates and README
Add the Obsidian vault template files and project README so users can get set up immediately.

- [ ] Write `vault_templates/Pantry.md` — example ingredient inventory with category headings (spirits, liqueurs, mixers, juices, syrups, bitters, garnishes)
- [ ] Write `vault_templates/Preferences.md` — example taste profile with likes/dislikes sections
- [ ] Write `vault_templates/Cocktail Log.md` — example log with a sample rated entry
- [ ] Write `vault_templates/Cocktail Suggestions.md` — example output file showing the expected suggestion format
- [ ] Generate `README.md` using the readme-generator skill

**Commit message:**
```
docs: add vault templates and README

Obsidian vault template files give users a ready-to-go setup.
README documents installation, configuration, and usage.

[CC-2]
```
