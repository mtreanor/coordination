# Works have steps, report events in a shared vocabulary, and Runs are described by config files

Decided Nov 7, 2026, so that different works can be switched in and out of the same harness and the same social world. This revises the `Work` interface of ADR 0004; the `SocialLayer` interface is unchanged.

## 1. A round of work can have several steps

A work round can be a sequence of steps with information revealed in between. In the Investment Club, for example, everyone invests, then each business sees its project's return and pays back each investor. Each step is a set of simultaneous **work decisions**. A work decision is one question for one agent: a key, a prompt and a menu.

```python
class Work(Protocol):
    name: str
    agents: list[str]
    def next_round(self) -> None                     # start the next round
    def decisions(self) -> list[WorkDecision]        # the decisions due now; [] means the round is done
    def resolve(self, answers: dict[str, int | None]) -> list[WorkEvent]   # by decision key
    def briefing(self, agent) -> str
    def state(self) -> list[WorkFact]                # mirrored into the social world
    def record(self) -> dict                         # ground truth for the log, never mirrored
    def over(self) -> bool
    def scores(self) -> dict[str, float]
```

A work is constructed as `Work(agents, seed=..., rounds=None)`. Its rules, amounts and odds are in code; `rounds=None` means the work's own length, and the override exists only for short test Runs. The Run calls `next_round`, then asks for and resolves decisions until there are none, then runs the Mirror and one social round. So the social channel runs between rounds, never between a round's steps.

`record()` exists for ground truth that agents must never see and that RUE must not read, such as the Investment Club's project returns. It goes into `rounds.jsonl` for analysis (judgement accuracy), not into RUE.

## 2. Work events use a shared vocabulary

*Replaced by ADR 0006 (Nov 7, 2026): work events report what changed and who is credited, instead of a category.*

There is **one social world for every work** (Mike, Nov 7). Its rules can't match on each work's own kinds of event, so each work event carries:

- **`kind`**: the work's own words ("invested in"), kept in the occurrence's text and data;
- **`category`**: one of a small shared list, which `RueSocial` registers as the occurrence's `actionType`, so the social world's rules match on it;
- **`amounts`**: the numbers the witnesses saw, named by the category, registered as numeric roles (`AMOUNT`, `STAKE`). RUE gets the numbers, not a verdict (Mike, Nov 7).

The vocabulary is in `src/coordination/work/vocabulary.py`. Version 0:

| Category | Meaning | Amounts |
|---|---|---|
| `helped` | The actor gave the target something, at its own cost | `amount`: what the target got |
| `took from` | The actor took something from the target | `amount`: what the target lost |
| `entrusted` | The actor put something in the target's hands, to be returned at the target's discretion | `amount`: what was handed over |
| `repaid` | The actor returned something to a target who had entrusted it | `amount`: what came back; `stake`: what the target had entrusted |

A category describes what the witnesses observed, never a judgement. "Repaid 5 on a stake of 10" is an observation; whether that's stingy or unlucky is for the social world to decide. Abstracting each work into these terms is the open design problem: the list is expected to grow and change as the social world is authored, and a new work may need a new category.

## 3. A Run is described by a config file

The work's rules are code; a Run's settings are a TOML file in `configs/`: the work, the agents, the Situation, the social layer and its tick plan, the choosers, the seed. `scripts/play.py configs/<name>.toml` plays it, and command-line flags override the file. Every Run directory gets the resolved settings and the git commit as `config.json`, the manifest the preregistration needs.

## Consequences

- `StubWork` becomes a one-step round.
- The agents come from the Run config (or the work's default). The Run config is the source of truth for who is in a Run; the RUE scenario declares what an agent is. RUE takes its agents only from the scenario's `entities.json`, so the two are **kept in sync by hand** (Mike, Nov 7: no change to RUE for this). Before a Run asks anything, the harness reads that file and stops, naming what to add or drop, unless it declares exactly the Run's agents; a test checks every config in `configs/` the same way, and `RueSocial.start` checks the live session again. A Situation that names an agent the Run doesn't have is an error.
- Not being dealt with at all (for example, receiving no investments) is not a work event. The work reports it in that agent's Briefing only.
