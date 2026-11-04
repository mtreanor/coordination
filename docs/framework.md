# The Run framework

How a Run is put together, and how to slot in a new version of the work or the social layer. The decision behind it is ADR 0004.

## A round

| # | Phase | Owner | What happens |
|---|---|---|---|
| 1 | Work moves | Work | Each agent gets its Briefing and picks a work move from an unscored menu |
| 2 | Resolve | Work | All work moves apply at once; the work reports work events (kind, actor, target, witnesses) |
| 3 | Mirror | Social layer | The work state (`Work.state()`, e.g. points) is copied into the social world as it is. Nothing is judged |
| 4 | Record | RUE (`record-work-events`) | Each work event becomes an occurrence its witnesses can judge |
| 5 | Work judgement | RUE (`work-judgement`) | Each witness picks a judgement action for each work occurrence |
| 6 | Social actions | RUE (`social-actions`) | Each agent picks a social action (once per time the tick plan lists the phase) |
| 7 | Social judgement | RUE (`social-judgement`) | Each listener picks a judgement action for what was said |

Every Briefing has two parts: the work's text (`Work.briefing`) and the social world's text (`SocialLayer.briefing`, every `briefing` template in the agent's private store). With `--social off` (the work-only condition), phases 3–7 do nothing and the Briefing has only the work. Phases 4–7 are **one RUE tick of the scenario's tick plan**, as in reception: the plan decides which phases run and in what order, so you can add rulesets between them or step a whole social round in the authoring tool's Play tab. Conditions are tick plans, chosen with `--plan`: stub-social has `full` and `no-judgement` (phases 5 and 7 left out). With `--rue-judgement`, RUE's ranking picks the judgement actions instead of the agents. Agents are asked only at the stages they choose in; the record stage always runs unasked.

## Files

| Path | What it is |
|---|---|
| `src/coordination/run.py` | `Run`: sequences the phases and builds every Decision Request |
| `src/coordination/work/` | `Work`, `WorkEvent`, and `WorkFact` (mirrored state); `StubWork`; the `WORKS` registry |
| `src/coordination/social/` | `SocialLayer` (`start`, `briefing`, `mirror`, `social_round`), `NoSocial`, `RueSocial`; the `SOCIAL_LAYERS` registry |
| `src/coordination/situation.py` + `situations/*.toml` | Situations: principal instructions and starting RUE facts |
| `rue-data/stub-social/` | The stub social world as a RUE scenario |
| `scripts/play.py` | Runs one Run from the command line |

A Run writes `decisions.jsonl` (every Decision Request and answer, with round and phase), `events.jsonl` (work events per round), and `rounds.jsonl` (scores and each agent's social Briefing after each round) to `runs/<time>-<work>-<social>-<situation>/`.

## Adding a new work

1. Write a class with the `Work` methods: `briefing`, `options`, `state`, `resolve`, `over`, `scores`, plus `name` and `agents`. Its briefing shows only what that agent may know (ADR 0003).
2. Report every work move another agent should be able to judge as a `WorkEvent`, with its witnesses, and return the work state to mirror from `state()`.
3. Register it in `WORKS` (`src/coordination/work/__init__.py`).
4. In the RUE scenario, declare a predicate for each mirrored `WorkFact`, and a `report_<kind>` predicate and a `record-work-events` action for each work event kind.

## Adding a new social world

Usually this is a new RUE scenario, not new Python. Copy `rue-data/stub-social/`, add it to `project.config.json`, and run with `--scenario <name>`. `RueSocial` expects:

- an `agent` type with private stores, matching the work's agents;
- a predicate for each mirrored piece of work state, and `report_<kind>(actor, target)` predicates for the work's event kinds;
- tick plans (one per condition), each a list of phases for the social round: first a phase that records each `report_<kind>` as an occurrence (stub-social: `record-work-events`), then the judgement and social action phases;
- stages with distinct names, because a stage's name decides whether agents are asked there and is the phase name in the logs. `RueSocial` asks agents at `work-judgement`, `social-actions` and `social-judgement` (configurable as `agent_stages`), with the acting agent bound as `?SELF` or `?JUDGE`; judgement stages loop over `?JUDGE` and `?OCC`;
- a `briefing` text template on every predicate the agent should see.

A social layer that isn't RUE at all implements `SocialLayer` and goes in `SOCIAL_LAYERS`.

## Stubs

Both stubs exist to exercise the loop, not to be studied.

- **StubWork:** each round, each agent's work move is to do its own work (+1 for itself), helps a colleague (+2 for them), or takes from a colleague (+2 for itself, −2 for them). Points are private; only the two agents involved see a help or a take.
- **stub-social:** dispositions `likes` and `trusts` (0–10, everyone starts at 5), and mirrored `points`. Work judgement actions: resent / benefit of the doubt / grateful / suspicious / no real opinion. Social actions: complain about someone, speak well of someone, stay quiet. Social judgement actions: take it to heart / doubt it / no real opinion.

## Known limits

- A pair can have only one work event of each kind per round (recording groups by actor and target).
- The rounds are visible in the stub's Briefing, which invites end-game defection; the real work decides whether the end is known.
- Each social-actions phase is one pass. For more, list the phase more than once in the tick plan; there's no early stop when everyone stays quiet.
- The agents see RUE's utilities beside social actions and judgement actions unless `--hide-scores`; at least one model said it followed them.
