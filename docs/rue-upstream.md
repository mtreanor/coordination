# RUE upstream work

Features this project needs from RUE, to be built in the RUE repo as general features (documented there, usable by any RUE application). Nothing here is started unless marked.

## Done

- Unbounded numerics: an omitted `minValue`/`maxValue` means unbounded, and an omitted `default` is 0.
- Choice records: each ActionRecord records who chose the action (policy, player, or agent) and why.
- The RUE server lives in `src/server/`; the authoring tool mounts its routes onto it.
- Predicate text templates: a predicate's `toString` in `predicates.json` maps any names to templates using `{args[N]}`, `{value}`, and `{tier}`; placeholders that can't be filled stay as written. Rendered with `engine.renderFacts(name, { owner })`, `GET /templates`, and `POST /render`, and edited in the tool's predicate editor. See RUE's `docs/schema.md#tostring`.

- Unchanged numeric sets add no history (Nov 7 2026): setting a number to the value it already holds is not recorded, so rules that re-set values every tick don't fill provenance with repeats. Test: `tests/NumericSetHistory.test.js`.
- Fresh priming (Nov 7 2026): a stage's priming entry with `"fresh": true` first clears the ephemeral numerics its ruleset writes, so priming recomputes from the current facts on every run instead of adding up across loop invocations and stages. A checkbox on each priming rule in the tool's stage editor. See RUE's `docs/actiongraph-tickplan.md#fresh-priming`. Test: `tests/plan/TickPlan.fresh.test.js`.
- Reasons (Nov 7 2026): `engine.reasonsFor(candidate)` renders the facts behind a candidate's utility (the premises of the rules that set the numerics it reads) with a named text template, marked for or against, with no utility, value or weight; the Play server serves them on every candidate, and `/config` takes `reasonTemplate`. A `{text[N]}` placeholder renders an occurrence's text. See RUE's `docs/actions.md#reasons`. Tests: `tests/Reasons.test.js`.
- `renderFacts` with `skipDefaults` (Nov 7 2026): leaves out numeric facts at their predicate's default, so a briefing doesn't spell out neutral values.

## External actions (built Nov 5 2026)

An **external action** is something that happened outside RUE (a work event) and is registered in RUE as if it had been an action. It is not declared in RUE beforehand: its kind, its roles and its state changes are open. RUE never picks it and never offers it on a menu. Once it's registered, it looks just like an internal action to rules, and its provenance leads to where it was reported from. RUE assumes nothing about how it came about: someone may have chosen it, or nothing did. Any other field is an error.

**The call.** `engine.performExternal({ actionType, roles, effects, text, source, ref, data })`, served as `POST /play/:scenario/external` with the same body.

| Field | Required | What it is |
|---|---|---|
| `actionType` | yes | Any non-empty string: the kind of thing that happened |
| `roles` | no | A map from role name to value. Values may be entity names, other strings, numbers or booleans |
| `effects` | no | State changes, each in RUE's effect syntax: assert, `not` (retract), `= N`, `+= N`, `-= N`, and owner-prefixed private-store writes. They may use `?occ` (the new occurrence) and `?NAME` for any role |
| `text` | no | A readable description, kept as the action's content (`?NAME` placeholders fill from the roles) |
| `source`, `ref` | no | Where it came from: a system name, and that system's reference for it |
| `data` | no | Any JSON kept with it; RUE stores it and never reads it |

**What RUE does**, matching an internal action that has `record(?occ)` as its first effect:

1. It validates everything before changing anything. If one effect is wrong, nothing is applied.
2. It mints `occN` (type `occurrence`), using the same counter as `record()`.
3. It asserts `actionType(occN, actionType)` and `role(occN, NAME, value)` for each role. If the kind is new, it registers the kind as an `action` entity so that queries like `actionType(?o, ?k)` find it.
4. It applies the effects at the current tick.
5. It writes one ActionRecord to the action log. The record holds the tick, the binding (the roles plus `occ`), `utilityBreakdown: null`, `occurrence: "occN"`, `external: { source, ref, data }`, and `choice: null` (nothing in RUE selected it). Every fact the call asserts or changes carries action-effect provenance to that record.

**Validation: the schema is the contract.** Every effect must use a declared predicate, with the declared number of arguments. Boolean predicates are asserted or retracted; numeric ones are set or adjusted. Each argument must fit its declared type: if a type has registered entities, the value must be one of them. A type with no registered entities is open, the way `role`'s value slot is. A variable must be `?occ` or a role. An owner must have a private store. The role names `occ` and `this_action` are reserved. The call is refused while a tick is in progress (paused at a choice).

**Not included yet:** creating or removing entities in effects; tick-end queuing (effects apply at once); running rulesets on registration (the tick plan does that).

**How this project uses it.** `RueSocial` turns each `WorkEvent` into one external action: the kind, the roles `SELF` (actor) and `OTHER` (target), `witnessed(?occ, W)` for each witness but the actor, and `work_occurrence(?occ)`, with source `work` and the round as `ref`. Who acted is this project's own convention, carried by the `SELF` role; RUE has no notion of an actor. The work stays RUE-agnostic. The `report_*` predicates and the `record-work-events` phase are gone.

## Still to do

- Premise linking: rule-derived facts link to the specific facts that triggered them.
- A seed parameter on `/play/:scenario/start`.
- Bulk provenance export for analysis.
- Perspective in text templates (Mike, Nov 7 2026). Templates now quietly assume their reader is `args[0]`: `friends` renders "You count them as a friend." because every private fact rendered so far is one the reader holds about someone else, and a world fact, or a view rendered for an observer or a log, would come out wrong. The template system should assume nothing about "you". Proposed: a template may give perspective forms, called out explicitly, e.g. `"state": {"third": "{args[0]} likes {args[1]} {value} out of 10.", "second": "You like {args[1]} {value} out of 10."}`; rendering (`renderFact`, `renderFacts`, `reasonsFor`, `POST /render`, served reasons) takes a `viewer`, and uses the `second` form when `args[0]` is the viewer and the template has one, else `third`. A plain-string template stays as it is. Every sentence stays authored and deterministic: no substitution of "you" (it breaks agreement: "you likes"), no NLG outside RUE. Then this project's templates name both people (no "them"), and the `state`/`reason` split in `predicates.json` may collapse into one template.
