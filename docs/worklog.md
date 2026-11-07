# Work log

What was worked on, when, and for roughly how long, for the hackathon report. Times are local (US Eastern). Kept up to date during sessions; entries before Nov 7 10:24 are reconstructed from commit times, file creation times and session logs, so they show when work happened, not exact hours spent.

## Summary by area (hackathon, Nov 6 onward)

| Area | Approx. time | When |
|---|---|---|
| Hackathon setup: README of what existed before, round-loop figure, report template | 0.5 h | Nov 6, 15:30–16:00 |
| Experiment design: preregistration draft, Feinberg et al. (2014) notes, future work | 2.5 h | Nov 6, 16:00–18:40 |
| Work design and build: paradigms survey, the Investment Club (design, code, tests), steps in a round, Run configs (ADR 0005) | 3 h | Nov 6, ~21:30 – Nov 7, 00:30 |
| Work design and build: Not My Bug (design, code, tests), pilot config | 1 h | Nov 7, ~09:30–10:20 |
| Interface between the work and RUE (social layer) | 3.5 h so far | Nov 7, 10:24–13:45 |

## Before the hackathon

| When | What |
|---|---|
| Sep 30 – Oct 1 | Project set up; RUE as a submodule; a proof of concept driving RUE from Python; model choosers (local and hosted); Briefings from RUE's text templates |
| Nov 3 – Nov 4 | Campfire scenario and design docs; game candidates (the Harbor, the Review Queue, the Firm); the Run framework; the social round as one tick of a tick plan |
| Nov 6, early | Work events registered in RUE as external actions |

## Hackathon log

### Nov 6

- **15:30–16:00, setup.** README describing what existed before the hackathon; round-loop figure; the report template.
- **16:00–18:40, experiment design.** Preregistration draft (conditions, measures, analysis); notes on Feinberg, Willer & Schultz (2014); future work.
- **~21:30 – Nov 7 00:30, work design and build.** Survey of experimental-economics paradigms; the Investment Club chosen and built; works with several steps per round, a shared event vocabulary and Run configs (ADR 0005).

### Nov 7

- **~09:30–10:20, work design and build.** Not My Bug designed and built; a pilot config for switching games.
- **10:24–, the interface between the work and RUE.**
  - Started RUE's authoring tool on this project's data; renamed the scenario `stub-social` → `social-layer-data` and made it the default; removed the `no-judgement` condition.
  - Explored how work events become RUE predicates: shared categories, then a translation ruleset per game (prototyped, then dropped), then effects reported directly by the work (ADR 0006). Fixed RUE so re-setting a number to its current value adds no history.
  - Rewrote the stub judgement actions so one set judges every work.
  - Revisited the interface around responsibility and minimal interference, and built it (ADR 0006, rewritten): events report what literally changed (`change(occ, agent, quantity)`) and who is credited (`responsible`, public, witnessed, or none); a new attribution phase lets an agent hold someone responsible when credit is unknown; a labelling phase replaces work judgement. Not My Bug now reports hours lost to handoffs as an occurrence nobody is credited with. RUE's private-store fallback collapses public, witnessed and assigned credit into one predicate, so no derived predicates were needed.
  - Labels now only record what an agent calls an occurrence; a ruleset phase after labelling turns them into changes in likes and trusts (where the social world's own rulesets will go). Removed `--rue-judgement`, which let RUE's ranking choose attributions and labels for the agents.
  - Corrected the model of how social facts reach choices (Mike): actions change state; priming rulesets, run just before a stage scores its actions, set ephemeral **impulses** that utilities read; labels are social facts on the left-hand side of priming rules. Dropped the label-consequences ruleset; every stub action's utility is now an impulse; empty priming rulesets attached to attribution, labelling and social actions for Mike to author. Gave social judgement the same impulses and priming slot. Merged attribution and labelling into one work judgement stage: a label that names someone holds them responsible (`couldBeResponsible` collapses "the one you know did it" and "anyone, when you don't know"). Replaced the per-action impulses with six shared ones (warm, hostile, trusting, wary, charitable, reserved) that every utility sums, primed by one `social-priming` ruleset; impulses may go negative.
  - Added fresh priming to RUE: a stage's priming entry can clear the ephemerals its ruleset writes before running, so priming recomputes instead of adding up across loop invocations and stages. A checkbox on each priming rule in the authoring tool's stage editor. `social-priming` is now the priming rules of all three stages, marked fresh. (First built as tick plan ruleset phases; moved to stage priming at Mike's direction.) Added `leftAlone(agent)`, a derived fact (nobody did anything to you this round that you can put a name to), the general form of "nobody invested in you".

## Notes for the report

- **Interfere as little as possible with the LLM's strategy** (Mike, Nov 7). The social layer records what happened and who is responsible where that's public; it doesn't tell an agent whether an outcome was good or bad for it, or how much, since that depends on the agent's own strategy. Interpretation (who to hold responsible when it isn't public, what to call an occurrence) is the agent's choice; RUE never makes it for them (the option for RUE's ranking to choose was removed).
