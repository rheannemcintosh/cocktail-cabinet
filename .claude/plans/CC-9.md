# Plan: CC-9

## Work Item
**Title:** Bartender agent

## Overview
CC-9 builds the bartender agent — the first of three specialist agents in Cocktail Cabinet's multi-agent planning pattern. The agent uses a bartender system prompt and takes the categorised pantry and mood/flavour profile as structured input, returning 2-3 ranked cocktail suggestions with ingredient match scores. Its output feeds directly into the shopper (CC-10) and taste (CC-11) agents, and replaces the current single-prompt recipe generation step in the orchestrator.

## Phases

### Phase 1: Create branch plan
Commit the branch plan so it is tracked in git from the start of the branch.

- [X] Create `.claude/plans/CC-9.md`

**Commit message:**
```
docs: add branch plan for CC-9

Documents the implementation phases for the bartender agent,
the first specialist agent in the multi-agent planning pattern.

[CC-9]
```

### Phase 2: Bartender agent
Build the bartender agent with a system prompt and structured output. Using a system prompt with the Gemini SDK distinguishes this from the plain generate() calls in the orchestrator, making the multi-agent pattern clearly visible.

- [X] Write `src/agents/bartender.py` with `suggest(pantry: dict, flavour_profile: dict) -> list[dict]`
- [X] Define a `SYSTEM_PROMPT` constant that gives the agent its bartender persona, instructs it to rank suggestions by ingredient availability, and specifies the JSON output format
- [X] Use `client.chats.create(config=GenerateContentConfig(system_instruction=SYSTEM_PROMPT))` to initialise the agent with a system prompt
- [X] Parse the JSON response into a list of cocktail dicts, each with `name`, `ingredients` (list of `{name, in_pantry: bool}`), and `match_score` (int, ingredients in pantry / total ingredients)
- [X] Add module and function docstrings

**Commit message:**
```
feat: add bartender agent with system prompt and structured output

Bartender agent uses a Gemini system prompt to suggest 2-3 cocktails
ranked by pantry match score, returning structured JSON for downstream
agents to consume.

[CC-9]
```

### Phase 3: Orchestrator integration
Replace the current single generate() recipe step in the orchestrator with a call to the bartender agent, so the multi-agent pattern is wired into the main flow.

- [X] Update `src/orchestrator.py` to import and call `bartender.suggest(pantry, flavour_profile)` in place of the direct recipe generation prompt
- [X] Pass the bartender's structured output to `write_suggestion()` as formatted markdown

**Commit message:**
```
refactor: wire bartender agent into orchestrator

Replaces the single recipe generation prompt with a call to the
bartender agent, establishing the multi-agent handoff pattern.

[CC-9]
```

### Phase 4: Tests
Write tests for the bartender agent using mocked Gemini calls, and update the orchestrator test to reflect the new agent-based flow.

- [ ] Write `tests/test_bartender.py` — unit tests mocking the Gemini chat to assert the system prompt is set, the pantry and flavour profile appear in the message, and the response is parsed into a correctly structured list
- [ ] Update `tests/test_orchestrator.py` — replace the mocked `generate()` call with a mock of `bartender.suggest()` and assert it is called with the correct pantry and flavour profile

**Commit message:**
```
test: add tests for bartender agent and update orchestrator tests

Unit tests verify the system prompt, input context, and structured
output parsing. Orchestrator tests updated for the agent-based flow.

[CC-9]
```
