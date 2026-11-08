# Saved Runs

The Runs behind `docs/findings.md`, copied from `runs/` (which is gitignored) so the claims stay backed. Each directory is a Run as `scripts/play.py` writes it: `config.json` (resolved settings, chooser per agent, commit), `rounds.jsonl` (per sprint: work moves, scores, each agent's social state), `events.jsonl` (work events and who witnessed them), `decisions.jsonl.gz` (every Decision Request in full, with the chosen option and the agent's rationale), and `play.log` where there was one.

Summarise any of them with `uv run scripts/summarise_runs.py findings/runs/<run>`.

All: Not My Bug, alice, bob, carol, dave, 10 sprints, gemini-flash, seed 0.

| Directory | Social layer | Situations | Notes | Original |
|---|---|---|---|---|
| `neutral-defector-social` | rue (`full`) | `bob-defects` | F1 | `runs/batch-goal-2x2/neutral-defector-seed0` |
| `neutral-defector-workonly` | off | `bob-defects` | F1 | `runs/batch-neutral-defector-off/off-seed0` |
| `neutral-social` | rue (`full`) | none | F1 baseline, F2 | `runs/batch-goal-2x2/neutral-seed0` |
| `noinstr-workonly` | off | none | F1 baseline, F2; no goal line yet | `runs/batch-neutral-vs-off/off-seed0` |
| `history-social` | rue (`full`) | `office-history` | F2 | `runs/batch-goal-2x2/history-seed0` |
| `history-defector-social` | rue (`full`) | `office-history`, `bob-defects` | F2 | `runs/batch-goal-2x2/history-defector-seed0` |
| `oldinstr-workonly` | off | (the old `neutral`) | F2; older code, old default instruction | `runs/20261107-170053-not-my-bug-off-neutral` |

Every Run was made from uncommitted code (commit `2d9a777…-dirty`).
