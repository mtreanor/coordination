# The Run framework

How a Run is put together, and how to slot in a new version of the work or the social layer. The decision behind it is ADR 0004.

## A round

| # | Phase | Owner | What happens |
|---|---|---|---|
| 1 | Work moves | Work | Each agent with a work decision this step gets its Briefing and picks a work move from an unscored menu |
| 2 | Resolve | Work | The step's work moves apply at once; the work reports work events (kind, actor, target, witnesses, and their effects in shared predicates, ADR 0006). Phases 1–2 repeat for each step of the work's round (ADR 0005) |
| 3 | Mirror | Social layer | The work state (`Work.state()`, e.g. points) is copied into the social world as it is. Nothing is judged |
| 4 | Record | Social layer → RUE | Each work event is registered as an external action: an occurrence its witnesses can judge |
| 5 | Work judgement | RUE (`work-judgement`) | Each witness labels each work occurrence; a label naming someone holds them responsible (ADR 0006) |
| 6 | Social actions | RUE (`social-actions`) | Each agent picks a social action (once per time the tick plan lists the phase) |
| 7 | Social judgement | RUE (`social-judgement`) | Each listener picks a judgement action for what was said |

Every Briefing has two parts: the work's text (`Work.briefing`) and the social world's text (`SocialLayer.briefing`, every `briefing` template in the agent's private store). With `--social off` (the work-only condition), phases 3–7 do nothing and the Briefing has only the work. Phases 5–7 are **one RUE tick of the scenario's tick plan**, as in reception: the plan decides which phases run and in what order, so you can add rulesets between them or step a whole social round in the authoring tool's Play tab. Conditions are tick plans, chosen with `--plan`: social-layer-data has `full`. Agents are asked only at the stages they choose in.

## Files

| Path | What it is |
|---|---|
| `src/coordination/run.py` | `Run`: sequences the phases and builds every Decision Request |
| `src/coordination/work/` | `Work`, `WorkDecision`, `WorkEvent`, and `WorkFact` (mirrored state); `StubWork`, `InvestmentClubWork`, `NotMyBugWork`; the `WORKS` registry |
| `src/coordination/config.py` + `configs/*.toml` | Run configs: which work, agents, Situation, social layer and choosers a Run uses |
| `src/coordination/social/` | `SocialLayer` (`start`, `briefing`, `mirror`, `social_round`), `NoSocial`, `RueSocial`; the `SOCIAL_LAYERS` registry |
| `src/coordination/situation.py` + `situations/*.toml` | Situations: principal instructions and starting RUE facts |
| `rue-data/social-layer-data/` | The stub social world as a RUE scenario |
| `scripts/play.py` | Runs one Run from the command line |

A Run writes `config.json` (its resolved settings and git commit), `decisions.jsonl` (every Decision Request and answer, with round and phase), `events.jsonl` (work events per round), and `rounds.jsonl` (scores, the work's ground-truth `record()`, and each agent's social Briefing after each round) to `runs/<time>-<work>-<social>-<situation>/`.

## Adding a new work

The interface is ADR 0005's. A work's rules are code; which work a Run plays is in its Run config.

1. Write a class with the `Work` methods, constructed as `Work(agents, seed=..., rounds=None)`:
   - `next_round()`, then `decisions()` and `resolve(answers)` for each step of the round, until `decisions()` is empty. A round with one step (`StubWork`) returns its decisions once; the Investment Club has two steps (invest, then pay back). A `WorkDecision` is one question for one agent: a `key`, a `prompt` and a menu. Answers come back by key.
   - `briefing(agent)`: only what that agent may know (ADR 0003).
   - `state()`: the work state to mirror. Every work mirrors each agent's score as `points(agent)`.
   - `record()`: ground truth for the log only, such as hidden dice. Never mirrored.
   - `over()`, `scores()`, plus `name`, `agents` and `default_agents`.
2. Report every work move another agent should be able to judge as a `WorkEvent`: its own `kind` and `text`, its `actor` (ground truth for the log), its `witnesses`, its `credit` (`"witnesses"`, `"public"` or `"none"`), and what literally changed for each agent in your own quantities (`changes`, e.g. `{"carol": {"hours": -2}}`). Never whether a change was good or bad: that's for each agent's strategy (ADR 0006). With no credit, the text must not name the actor.
3. Register it in `WORKS` (`src/coordination/work/__init__.py`) and write a Run config in `configs/`.

Work events need nothing declared in RUE beyond the shared predicates: each is registered as an external action whose actionType is the event's kind (a label no rule matches on), and whose effects set `witnessed`, `change(occ, agent, quantity)`, and `responsible`: in the world when the credit is public, in each witness's own store when only the witnesses know, nowhere when nobody does. `responsible` falls back to the world, so `?A.responsible(occ, ?X)` finds public, witnessed and assigned credit in one query.

## Run configs

A Run's settings are a TOML file in `configs/` (`src/coordination/config.py`): the work, the agents (the work's defaults otherwise), the Situation, the social layer and tick plan, the choosers (a default and per-agent overrides), the seed, and optionally `rounds` for a short test Run. `uv run scripts/play.py configs/<name>.toml` plays it; command-line flags override it. The Run directory gets the resolved settings and the git commit as `config.json`.

| Config | What it is |
|---|---|
| `configs/stub.toml` | The stub work with the RUE social world |
| `configs/investment-club.toml` | The Investment Club's eight businesses, work-only, with two planted defectors (`situations/club-defectors.toml`) |
| `configs/pilot.toml` | Five agents with bo as a planted defector (`situations/one-defector.toml`), work-only. Switch games by changing `work` alone |
| `configs/not-my-bug.toml` | Not My Bug's five engineers, work-only, random choosers |
| `configs/not-my-bug-rue-smoke.toml` | Not My Bug with the social world's four agents, three sprints: a smoke test of the RUE path |
| `configs/investment-club-rue-smoke.toml` | The Investment Club with the social world's four agents, three rounds: a smoke test of the RUE path |

## Adding a new social world

Usually this is a new RUE scenario, not new Python. Copy `rue-data/social-layer-data/`, add it to `project.config.json`, and run with `--scenario <name>`. `RueSocial` expects:

- an `agent` type with private stores, declaring exactly the Run's agents in `entities.json`. This is kept in sync by hand: `scripts/play.py` stops before the Run, naming what to add or drop, if it doesn't match, and `tests/test_investment_club.py` checks every config in `configs/`;
- a predicate for each mirrored piece of work state, plus `witnessed(occurrence, agent)` and `work_occurrence(occurrence)`, which `RueSocial.register` writes for each work event (roles `SELF` for the actor, `OTHER` for the target);
- tick plans (one per condition), each a list of phases for the social round: the judgement and social action phases. Work events are already occurrences when the tick starts;
- stages with distinct names, because a stage's name decides whether agents are asked there and is the phase name in the logs. `RueSocial` asks agents at `work-judgement`, `social-actions` and `social-judgement` (configurable as `agent_stages`), with the acting agent bound as `?SELF` or `?JUDGE`; judgement stages loop over `?JUDGE` and `?OCC`;
- a `briefing` text template on every predicate the agent should see.

A social layer that isn't RUE at all implements `SocialLayer` and goes in `SOCIAL_LAYERS`.

## Stubs

Both stubs exist to exercise the loop, not to be studied.

- **StubWork:** each round, each agent's work move is to do its own work (+1 for itself), helps a colleague (+2 for them), or takes from a colleague (+2 for itself, −2 for them). Points are private; only the two agents involved see a help or a take.
- **social-layer-data:** dispositions `likes` and `trusts` (0–10, everyone starts at 5), and mirrored `points`. Work judgement labels: selfish, careless, fair, generous (each naming someone the agent could hold responsible) / bad luck / no real opinion. Every action's utility is a sum of six shared impulses (warm, hostile, trusting, wary, charitable, reserved), set by one priming ruleset, `social-priming`, which every stage uses as its priming rules, marked fresh; it has no rules yet; `leftAlone(agent)` is derived (ADR 0006). Social actions: complain about someone, speak well of someone, stay quiet. Social judgement actions: take it to heart / doubt it / no real opinion.

## Known limits

- A work event reaches RUE with its actor (the `SELF` role) but not the reason for the work move; that is in `decisions.jsonl`, not in RUE.
- Mirrored work state (points) still arrives through `/assert`, so it isn't attributed to the work event that changed it.
- The rounds are visible in the stub's Briefing, which invites end-game defection; the real work decides whether the end is known.
- Each social-actions phase is one pass. For more, list the phase more than once in the tick plan; there's no early stop when everyone stays quiet.
- The agents see RUE's utilities beside social actions and judgement actions unless `--hide-scores`; at least one model said it followed them.
