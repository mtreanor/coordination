# The harness is Python and talks to RUE through the RUE server's HTTP API

RUE is JavaScript, so the path of least friction would be a Node harness calling the engine in-process. We chose Python for the game, harness, experiments and analysis instead, because that is what most AI-safety experiment work uses, and we reach RUE through a RUE server (split out of the authoring tool) with a documented, versioned API. A bonus is that a live Run can be watched in the authoring tool's UI.

## Consequences

- Changes to the RUE server API are expected to require changes here; pin the RUE submodule to a known commit.
- Parallel Runs use one RUE server process per Run.
- Bulk provenance export and a seed parameter are needed upstream.
