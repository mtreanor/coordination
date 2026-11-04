# The work lives outside RUE; RUE keeps a mirror of its state

The proposal had RUE generate the menu of both work moves and social actions. Instead, the work is a separate system that owns its state, decides which work moves are legal, resolves them, and owns the clock. RUE decides only social actions and judgement actions. After each resolution the Mirror copies the work state into RUE, where it becomes predicates that social rules can reason over; each mirrored fact carries external provenance pointing back to the work event that caused it.

We chose this so the work can be designed on its own terms, and so the work-only condition runs with no RUE at all, while still letting social reasoning see what happened in the work and letting provenance run from a belief all the way back to a work event.

## Consequences

- Work moves have no RUE ranking or provenance; only the social world does.
- RUE needs an external-event provenance type (a general RUE feature, not specific to this project).
- The social world reaches work moves without RUE ever modeling them: through the Briefing.

Terminology updated Nov 4, 2026 (game → work, Game Move → work move, Social Move → social action); the decision is unchanged. Inclinations, an optional second route from the social world to work moves, were dropped from the vocabulary the same day.
