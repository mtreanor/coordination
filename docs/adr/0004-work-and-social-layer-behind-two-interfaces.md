# The work and the social layer sit behind two interfaces, and everything but the work is RUE

A Run is some work plus some social layer, sequenced by `coordination.run.Run`. The work implements `Work` (`src/coordination/work/base.py`) and the social layer implements `SocialLayer` (`src/coordination/social/base.py`). Either can be swapped without touching the other: a new version of the work is a new `Work`, and a new social world is a new RUE scenario (or, rarely, a new `SocialLayer`).

The work is the only part that isn't RUE. The Mirror copies work state into RUE directly, with nothing judged. Every other social step is a RUE action chosen at a RUE selection point: recording work events as occurrences, judgement actions on work events (work judgement), social actions, and judgement actions on social actions (social judgement). The agent's work move is not a RUE action and is not scored. The principal's model deliberates freely and is only informed by RUE state, through its Briefing.

Decided Nov 4, 2026. This refines ADR 0001 (the work lives outside RUE) and makes the round in `docs/status.md` concrete.

## Consequences

- Every Decision Request, social or not, is built by the Run: the principal's instructions, the full Briefing (the work's text plus the social layer's text), the phase's prompt, and the menu. Social layers supply menus through an `ask` callback; they never talk to choosers directly.
- Work events are registered in RUE as external actions just before the tick. The social half of a round (work judgement, social actions, social judgement) is one RUE tick of the scenario's tick plan, as in reception. Conditions are tick plans (`--plan full`, `--plan no-judgement`). Whether agents or RUE's ranking pick the judgement actions is a Run setting (`--rue-judgement`).
- The work-only condition is `NoSocial`, so all conditions run through the same loop.
- Each work event reaches RUE as an external action (`docs/rue-upstream.md`): an occurrence of its kind, with roles `SELF` and `OTHER`, a `witnessed` fact for each witness but the actor, and provenance back to the work. (Until Nov 5, 2026, a `report_<kind>` fact and a recording phase stood in for this.)
