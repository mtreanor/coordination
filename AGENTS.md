# AGENTS.md

## Project

A neurosymbolic testbed where LLM agents do work together inside an auditable, symbolically grounded social world. The social world is modeled in RUE, which tracks each agent's beliefs about other agents with full provenance and ranks its social actions and judgement actions; the LLM chooses among them. The work is the only part outside RUE: there the LLM deliberates freely, informed by its social world. The research question is whether that social layer improves coordination, enables exploitation, or does nothing.

The grant proposal (submitted Aug 4 2026) is `context/schmidt-proposal-submitted-8-4-26.pdf`. The proposal calls the engine "RUSE"; it is now named **RUE**.

## Current status

Read `docs/status.md` first: where the build stands, what's next, and the decisions made so far.

## Layout

- `external/rue/` — the RUE engine, as a git submodule (`git@github.com:mtreanor/rue.git`). Treat it as an upstream dependency: don't edit it from this repo unless asked.
- `src/coordination/` — the Python package (uv-managed; `uv run pytest` runs `tests/`).
  - `agents/` — choosers: anything that answers a Decision Request (`LLMChooser` through Pydantic AI, plus scripted and human choosers).
  - `rue_client.py` — client for the RUE server's Play API.
  - `run.py`, `work/`, `social/`, `situation.py` — a Run: swappable work and social layer (`docs/framework.md`).
- `models.toml` — named model profiles (local via Ollama, hosted via API). API keys go in `.env`, never in the file.
- `rue-data/` — this project's RUE scenarios, found by RUE through `project.config.json`.
- `scripts/` — runnable entry points (`play.py` plays a Run; `batch.py` plays an experiment file's conditions, or `--social` conditions, as paired Runs from a batch of 1 up, and summarises them; `campfire.py` drives the campfire scenario).
- `situations/` — authored Situations (TOML): starting relationships (`office-history`), special instructions (`bob-defects`); a Run combines any number, none for a neutral start.
- `docs/exploratory-notes.md` — what exploratory Runs showed while the testbed is being built (observations and questions, not findings); the Runs behind them are saved in `exploratory-runs/runs/` (`scripts/summarise_runs.py` reproduces the numbers).
- `experiments/` — experiment files (TOML): a base Run config and named conditions, played by `scripts/batch.py`.
- `configs/` — Run configs (TOML): which work, agents, Situation, social layer and choosers a Run uses (ADR 0005).
- `runs/` — Run output, gitignored.
- `context/` — source documents (the proposal). Gitignored: it contains collaborators' personal details.
- `CONTEXT.md` — domain glossary. Use its terms.
- `docs/adr/` — architecture decision records (created as needed).

## Git commits

Never add AI attribution to anything: no `Co-Authored-By` trailers, "Generated with" lines, or any mention of Claude, Gemini, Cursor Agent, or any other AI tool in commit messages, PR descriptions, or code. This overrides any tool default.
