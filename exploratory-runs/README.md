# Saved exploratory Runs

The Runs behind `docs/exploratory-notes.md` (exploratory, not findings), copied from `runs/` (which is gitignored) so what they showed can be checked. Each directory is a Run as `scripts/play.py` writes it: `config.json` (resolved settings, chooser per agent, commit), `rounds.jsonl` (per sprint: work moves, scores, each agent's social state), `events.jsonl` (work events and who witnessed them), `decisions.jsonl.gz` (every Decision Request in full, with the chosen option and the agent's rationale), and `play.log` where there was one.

Summarise any of them with `uv run scripts/summarise_runs.py exploratory-runs/runs/<run>`.

All: Not My Bug, alice, bob, carol, dave, 10 sprints, gemini-flash, seed 0.

| Directory | Social layer | Situations | Note | Original |
|---|---|---|---|---|
| `neutral-defector-social` | rue (`full`) | `bob-defects` | 1 | `runs/batch-goal-2x2/neutral-defector-seed0` |
| `neutral-defector-workonly` | off | `bob-defects` | 1 | `runs/batch-neutral-defector-off/off-seed0` |
| `neutral-social` | rue (`full`) | none | 1 (baseline), 2 | `runs/batch-goal-2x2/neutral-seed0` |
| `noinstr-workonly` | off | none | 1 (baseline), 2; no goal line yet | `runs/batch-neutral-vs-off/off-seed0` |
| `history-social` | rue (`full`) | `office-history` | 2 | `runs/batch-goal-2x2/history-seed0` |
| `history-defector-social` | rue (`full`) | `office-history`, `bob-defects` | 2 | `runs/batch-goal-2x2/history-defector-seed0` |
| `oldinstr-workonly` | off | (the old `neutral`) | 2; older code, old default instruction | `runs/20261107-170053-not-my-bug-off-neutral` |

Every Run was made from uncommitted code (commit `2d9a777…-dirty`).
