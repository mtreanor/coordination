# The Coordination Game lives outside RUE; RUE keeps a mirror of its state

The proposal had RUE generate the menu of both resource and social moves. Instead, the Coordination Game is a separate system that owns game state, decides which Game Moves are legal, resolves them, and owns the clock. RUE only decides Social Moves. After each resolution the game pushes its state changes into RUE, where they become predicates that social rules can reason over; each mirrored fact carries external provenance pointing back to the game event that caused it.

We chose this so the game can be designed as a game on its own terms, and so the game-only baseline runs with no RUE at all, while still letting social reasoning see what happened in play and letting provenance run from a belief all the way back to a game event.

## Consequences

- Game Move rankings have no RUE provenance; only social state does.
- RUE needs an external-event provenance type (a general RUE feature, not game-specific).
- Social state reaches game decisions without RUE ever modeling game moves: through the Briefing, and optionally through Inclinations toward the other agents an option involves.
