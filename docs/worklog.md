# Work log

What was worked on, when, and for roughly how long, for the hackathon report. Times are local (US Eastern). Kept up to date during sessions; entries before Nov 7 10:24 are reconstructed from commit times, file creation times and session logs, so they show when work happened, not exact hours spent.

## Summary by area (hackathon, Nov 6 onward)

| Area | Approx. time | When |
|---|---|---|
| Hackathon setup: README of what existed before, round-loop figure, report template | 0.5 h | Nov 6, 15:30–16:00 |
| Experiment design: preregistration draft, Feinberg et al. (2014) notes, future work | 2.5 h | Nov 6, 16:00–18:40 |
| Future work: interpretability of social pressure, compute options | 0.75 h | Nov 6, 20:40–21:20 |
| Work design and build: paradigms survey, the Investment Club (design, code, tests), steps in a round, Run configs (ADR 0005), first LLM pilot | 1.5 h | Nov 6, 23:20 – Nov 7, 00:40 |
| Work design and build: Not My Bug (design, code, tests), pilot config, LLM pilot and menu fixes | 0.75 h | Nov 7, 09:35–10:20 |
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
- **20:40–21:20, future work.** Interpretability of social pressure in open models, written up at a less model-specific level; compute options (`docs/future-work.md`).
- **23:20 – Nov 7 00:40, work design and build.**
  - The W requirements reviewed; the Feinberg game written up as rules, then ruled out as the work, because gossip and social acts must be a completely separate channel (Mike).
  - Candidate business-themed works; the Investment Club (a trust game, Berg et al. 1995) written up as rules, placed in the literature (`docs/paradigms.md`), and given a worked example of three players over three rounds.
  - The swappable work interface (ADR 0005): work rounds with several steps, a shared event vocabulary, Run configs in `configs/` (the work's rules stay in code), and a check that the Run's agents match the RUE scenario's agents (kept in sync by hand; no change to RUE).
  - The Investment Club built and tested.
  - **First LLM pilot** (Claude Haiku, 8 businesses, 5 rounds, work-only, two planted defectors): everyone invested in whoever was listed first, so menus now list targets in a seeded random order. The rerun: partners lock in early, a fair payback after a ×1 project reads as stinginess, and the defectors were rarely invested in, so they had little chance to defect. About 10¢ a Run.

### Nov 7

- **09:35–10:20, work design and build.**
  - Not My Bug designed from Mike's "let them win" idea: whom you hurt (pass your bug) and whom you help ("Let me help"). Survival stakes considered and dropped (they'd make niceness a way to game the system); a public, unscored team velocity added instead.
  - Built and tested; `configs/pilot.toml` switches between the two works by changing one line.
  - **LLM pilot** (Haiku, 5 engineers, 8 sprints, work-only, one planted defector). The first run: agents misread which move pays. Menus now state each move's cost in hours, and Briefings spell out who cost whom what. The rerun: the defector passed his bug to the same colleague four sprints running, then stopped on his own in the last sprint; the victim noticed but never retaliated; nobody helped. 34 of 40 moves were "fix it yourself".
- **10:24–, the interface between the work and RUE.**
  - Started RUE's authoring tool on this project's data; renamed the scenario `stub-social` → `social-layer-data` and made it the default; removed the `no-judgement` condition.
  - Explored how work events become RUE predicates: shared categories, then a translation ruleset per game (prototyped, then dropped), then effects reported directly by the work (ADR 0006). Fixed RUE so re-setting a number to its current value adds no history.
  - Rewrote the stub judgement actions so one set judges every work.
  - Revisited the interface around responsibility and minimal interference, and built it (ADR 0006, rewritten): events report what literally changed (`change(occ, agent, quantity)`) and who is credited (`responsible`, public, witnessed, or none); a new attribution phase lets an agent hold someone responsible when credit is unknown; a labelling phase replaces work judgement. Not My Bug now reports hours lost to handoffs as an occurrence nobody is credited with. RUE's private-store fallback collapses public, witnessed and assigned credit into one predicate, so no derived predicates were needed.
  - Labels now only record what an agent calls an occurrence; a ruleset phase after labelling turns them into changes in likes and trusts (where the social world's own rulesets will go). Removed `--rue-judgement`, which let RUE's ranking choose attributions and labels for the agents.
  - Corrected the model of how social facts reach choices (Mike): actions change state; priming rulesets, run just before a stage scores its actions, set ephemeral **impulses** that utilities read; labels are social facts on the left-hand side of priming rules. Dropped the label-consequences ruleset; every stub action's utility is now an impulse; empty priming rulesets attached to attribution, labelling and social actions for Mike to author. Gave social judgement the same impulses and priming slot. Merged attribution and labelling into one work judgement stage: a label that names someone holds them responsible (`couldBeResponsible` collapses "the one you know did it" and "anyone, when you don't know"). Replaced the per-action impulses with six shared ones (warm, hostile, trusting, wary, charitable, reserved) that every utility sums, primed by one `social-priming` ruleset; impulses may go negative.
  - Added fresh priming to RUE: a stage's priming entry can clear the ephemerals its ruleset writes before running, so priming recomputes instead of adding up across loop invocations and stages. A checkbox on each priming rule in the authoring tool's stage editor. `social-priming` is now the priming rules of all three stages, marked fresh. (First built as tick plan ruleset phases; moved to stage priming at Mike's direction.) Added `leftAlone(agent)`, a derived fact (nobody did anything to you this round that you can put a name to), the general form of "nobody invested in you".
- **~14:00–14:10, stand-in social rules** (ahead of the Briefings). Bare-bones priming rules (liking and trust set the impulses) and label effects on likes and trusts, so social actions and social judgement now fire. Found that priming rules written over a fresh variable never prime the agent choosing (RUE keeps same-type variables distinct), so the acting agent is now `?SELF` in every stage and the rules are written about it.
- **~14:10–14:20, social actions.** Removed the starting state (every likes and trusts asserted at its default, 5). Social actions reworded as talk about a third party (complain to Y about X, praise X to Y), likelier told to friends; added confronting someone, which the one confronted can take to heart or resent.
- **~14:20–14:35, priming rules, tier 1.** Ran RUE's `author-utility-rules` process on `social-priming`: a first pass of 15 single-premise rules (likes, trusts, recent labels, `leftAlone`), chosen without item-by-item review for Mike to review later; the session manifest records what was considered and left out (nothing reads `change` or `points`). Found that a variable in a label slot matches nothing, so label rules name each label.
- **~14:35–14:50, agents choose freely.** Checked the pipeline end to end (random work moves, RUE's ranking for social choices: all three stages act, but zero-score ties fall to the first-listed label, "selfish"). Agents are now never shown RUE's ranking: no scores (the `--hide-scores` switch removed), and menus are shuffled and numbered by position, since RUE's order and ids were its ranking.
- **~14:50–15:15, Briefing design.** Agreed the design with Mike (ADR 0007): the work Briefing holds the agent's full RUE state; each RUE stage shows RUE's top five options in random order, each with its reasons (the provenance of its utility, rendered by RUE, no numbers about the ranking); doing nothing is a RUE choice. Reviewed the pipeline against it.
- **~15:15–15:35, Briefings, first fixes.** Menus are RUE's top five with ties broken at random; each judgement decision says what happened (work events' text; a social action's own text, remembered when it's chosen); a social decision's Briefing is the social world alone.
- **~15:35–16:20, reasons.** Added to RUE: `engine.reasonsFor(candidate)` renders the facts behind a candidate's utility (the premises of the rules that set the numerics it reads) with predicates' text templates, for or against, with no ranking numbers; the Play server serves them on every candidate; a `{text[N]}` template placeholder shows an occurrence's text. Here: `briefing` templates for `judgedAs` and `leftAlone`, reasons printed under each option, and a test that every predicate a priming rule reads has a template.

## Notes for the report

- **Interfere as little as possible with the LLM's strategy** (Mike, Nov 7). The social layer records what happened and who is responsible where that's public; it doesn't tell an agent whether an outcome was good or bad for it, or how much, since that depends on the agent's own strategy. Interpretation (who to hold responsible when it isn't public, what to call an occurrence) is the agent's choice; RUE never makes it for them (the option for RUE's ranking to choose was removed).
