# RUE upstream work

Features this project needs from RUE, to be built in the RUE repo as general features (documented there, usable by any RUE application). Nothing here is started unless marked.

## Done

- Unbounded numerics: an omitted `minValue`/`maxValue` means unbounded, and an omitted `default` is 0.
- Choice records: each ActionRecord records who chose the action (policy, player, or agent) and why.
- The RUE server lives in `src/server/`; the authoring tool mounts its routes onto it.
- Predicate text templates: a predicate's `toString` in `predicates.json` maps any names to templates using `{args[N]}`, `{value}`, and `{tier}`; placeholders that can't be filled stay as written. Rendered with `engine.renderFacts(name, { owner })`, `GET /templates`, and `POST /render`, and edited in the tool's predicate editor. See RUE's `docs/schema.md#tostring`.

## Still to do

- External occurrences and external-event provenance, so the game's events can be mirrored into RUE and traced.
- Premise linking: rule-derived facts link to the specific facts that triggered them.
- A seed parameter on `/play/:scenario/start`.
- Bulk provenance export for analysis.
