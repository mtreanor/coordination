# Coordination

A testbed where LLM agents, each acting for a different principal, do work together inside a social world they can see. The social world runs in **RUE**, a logic engine that tracks what each agent believes about the others, with full provenance. RUE also ranks the social actions (gossip, praise, staying quiet) and the judgements (resentful, generous, suspicious) available to each agent, and the agent's LLM picks among them. The work itself happens outside RUE: there the LLM deliberates freely, with its view of the social world in its prompt.

The research question: does a social layer like this improve coordination among agents, open new ways to exploit them, or do nothing? The first hypothesis to test is that **gossip leads to shunning, and shunning leads to reform**.

## Hackathon entry: Swarm Alignment Hackathon, Nov 6–8 2026

This repo is being entered in the Swarm Alignment Hackathon. **Everything up to the git tag `hackathon-start` existed before the hackathon.** That tag is in both this repo and the RUE submodule (`external/rue`). Only commits after it are weekend work.

### What existed before the hackathon

1. **RUE works.** It's a mature, separately developed engine with its own test suite and an authoring tool. It runs as a server that this project talks to over HTTP. Just before the hackathon it gained *external actions*, a way to register events that happened outside RUE, with full provenance.
2. **The testbed is sketched in code but hasn't really been tested.** A Run alternates a round of work with a social round in RUE. The work and the social layer each sit behind an interface, and both are stubs for now: a toy points game, and a placeholder social world with likes, trusts, complaining and praising. The loop runs end to end with random choosers and with a few LLMs. It hasn't produced results, and no real work or social world has been built.
3. **The idea.** We came into the weekend with a worked-out idea of what to build. It comes from a grant proposal to Schmidt Sciences that wasn't funded. The design notes in `docs/` (the experiment, candidate games, decisions) come from it.

## Layout

| Path | What it is |
|---|---|
| `external/rue/` | The RUE engine (git submodule) |
| `src/coordination/` | The Python package: the Run loop, the work, the social layer, the RUE client, and the agents (LLM, scripted and human choosers) |
| `rue-data/` | RUE scenarios: `stub-social` (the placeholder social world) and `campfire` (an earlier proof of concept) |
| `scripts/play.py` | Plays one Run from the command line |
| `situations/` | Authored starting conditions: principals' instructions and starting facts |
| `models.toml` | Named model profiles, local (Ollama) and hosted. API keys go in `.env` |
| `docs/` | Design notes. Start with `docs/status.md`, `docs/experiment.md` and `docs/framework.md` |
| `CONTEXT.md` | Glossary of the project's terms |

## Running it

Start the RUE server:

```bash
cd external/rue && npm install && npm run server
```

Then, in another terminal, play a Run with the stub work and the stub social world:

```bash
uv run scripts/play.py --chooser random --rounds 4
```

`--chooser` also takes a model profile name from `models.toml`, and `--social off` runs the work with no social layer. Output goes to `runs/`. Run the tests with:

```bash
uv run pytest
```
