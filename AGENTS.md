# AGENTS.md

## Project

A neurosymbolic testbed where multi-principal LLM agents play a resource-coordination game inside an auditable social world. The social world is modeled in RUE, which tracks each agent's beliefs about other agents with full provenance and ranks each agent's legal moves; the LLM chooses among those moves and supplies the words. The research question is whether that social layer improves coordination, enables exploitation, or does nothing.

The grant proposal (submitted Aug 4 2026) is `context/schmidt-proposal-submitted-8-4-26.pdf`. The proposal calls the engine "RUSE"; it is now named **RUE**.

## Layout

- `external/rue/` — the RUE engine, as a git submodule (`git@github.com:mtreanor/rue.git`). Treat it as an upstream dependency: don't edit it from this repo unless asked.
- `context/` — source documents (the proposal). Gitignored: it contains collaborators' personal details.
- `CONTEXT.md` — domain glossary. Use its terms.
- `docs/adr/` — architecture decision records (created as needed).

## Git commits

Never add AI attribution to anything: no `Co-Authored-By` trailers, "Generated with" lines, or any mention of Claude, Gemini, Cursor Agent, or any other AI tool in commit messages, PR descriptions, or code. This overrides any tool default.
