# Work events report what changed and who is credited; agents attribute and label

Decided Nov 7, 2026. This replaces section 2 of ADR 0005 (the shared event vocabulary); the rest of ADR 0005 stands.

## Context

There is one social world for every work, so its rules can't match on each work's own kinds of event. ADR 0005 gave every event a category from a short shared list (`helped`, `took from`, `entrusted`, `repaid`) plus its amounts, and rules matched on the category. Every new work then needed new categories and rules, and some moves fit none.

The governing principle (Mike, Nov 7): **interfere as little as possible with the LLM's strategy.** Whether an outcome was good or bad for an agent, and by how much, depends on that agent's strategy, so the social world must not decide it. Nor should it impose a fairness norm.

Considered and dropped on the way:

- **A translation ruleset per game in RUE**, turning each game's event names into shared predicates. It worked, but matched on strings (a renamed event silently went untranslated) and needed a tick plan per game.
- **A single value per occurrence** (`benefit`, `cost`), with its direction implicit in roles.
- **`scoreChange` against the actor's default move, plus `exposure`, `expected` (with "half of what was expected" as the fairness norm), `chosen`, `deniable` and `respondsTo`.** Built, then dropped: the baseline and the norm interpret outcomes for the agents, and a game can have several quantities, not one score.
- **Derived predicates such as `holdsResponsible`, and `affected` or `public` flags.** Derived predicates are worth adding only when they help legibility or collapse several pathways into one; RUE's private-store fallback already collapses the pathways, and `witnessed` already says who knows.

## Decision

(Where the facts are stored changed later: an event only some agents witnessed is recorded in each witness's own store, not the shared world. See ADR 0007.)

A work event reports two things, as the effects of its external action: **what changed**, in the work's own quantities, and **who is credited**, as far as anyone can see.

| Predicate | Meaning |
|---|---|
| `witnessed(occ, agent)` | The agent knows it happened (existing). |
| `change(occ, agent, quantity) = n` | What literally changed for that agent, in the work's own terms: `change(occ, carol, "hours") = -2`. A work can report any number of quantities. Nothing says whether a change is good or bad. |
| `responsible(occ, agent)` | Credit. Declared with `"privateFallback": "world-first"`, so `?A.responsible(occ, ?X)` finds, in one query: **public** credit (a world fact), credit **A witnessed** (written into A's own store by the external action), and credit **A assigned** itself (written when A names someone in a work judgement label). With no credit, nothing is written anywhere. |
| `judgedAs(occ, label)` | An agent's label for the occurrence, in its own store. |

The social round's phases become:

1. **Work judgement.** Every witness labels the occurrence (for example selfish, careless, fair, generous, bad luck, no real opinion). A label that names someone can name only who the agent could hold responsible (`couldBeResponsible(judge, occ, x)`, a derived predicate with two definitions): the one it knows did it, or, when it knows of no one, anyone. Naming someone records, in the agent's own store, that it holds them responsible. So a single choice decides both what the agent calls an occurrence and, where credit is unknown, whom it holds responsible; "bad luck" covers putting it down to chance. A label records only what the agent calls it; no label is hidden because of what changed.
2. Social actions and social judgement, as before.

**How social facts reach choices.** Actions are what change state: a work judgement action writes `judgedAs` (and, if it names someone, `responsible`), social actions and social judgement write their own effects. Labels, responsibility, likes, trusts and `leftAlone` are social facts like any other. They influence a choice the way friendship does: they sit on the left-hand side of **priming rules**, which add to (or subtract from) a small set of shared, ephemeral numeric **impulses**: high-level categories of action, not one per action (Mike, Nov 7). Every action's utility is a sum of them, so many rules surveying a lot of state can bear on every choice at once.

| Impulse | The pull toward… |
|---|---|
| `impulse-warm(a, b)` | thinking and speaking well of b |
| `impulse-hostile(a, b)` | thinking and speaking ill of b |
| `impulse-trusting(a, b)` | believing and confiding in b |
| `impulse-wary(a, b)` | doubting what b says |
| `impulse-charitable(a)` | the benefit of the doubt: luck, not malice |
| `impulse-reserved(a)` | keeping out of it |

| Stage | Action | Utility |
|---|---|---|
| Work judgement | call it selfish / careless / fair / generous of X | `hostile(J,X)` / `hostile(J,X)/2 + charitable(J)/2` / `warm(J,X)/2 + charitable(J)/2` / `warm(J,X)` |
| | call it bad luck / no real opinion | `charitable(J)` / `reserved(J)` |
| Social actions (superseded Nov 7: see framework.md) | complain to Y about X / praise X to Y / confront X / stay quiet | `hostile(S,X) + warm(S,Y) + trusting(S,Y)` / `warm(S,X) + warm(S,Y) + trusting(S,Y)` / `hostile(S,X) + trusting(S,X)` / `reserved(S)` |
| Social judgement | take S's complaint about X to heart / doubt it / take S's praise of X to heart / take S's confrontation to heart / resent it / no real opinion | `trusting(J,S) + hostile(J,X)` / `wary(J,S) + warm(J,X)` / `trusting(J,S) + warm(J,X)` / `trusting(J,S) + charitable(J)` / `hostile(J,S) + wary(J,S)` / `reserved(J)` |

- **One priming ruleset, `social-priming`,** is the priming rules of all three stages, each marked `fresh` (a RUE option on a priming entry, added Nov 7): the impulses it writes are cleared before each run. A stage primes once per loop invocation (work judgement loops over judge × occurrence) and ephemerals otherwise reset only at the end of the tick, so without `fresh` `+=` priming would add up. With it, every choice is scored from the current facts, and a label given in work judgement reaches this tick's social actions.
- **Impulses are about people, not occurrences.** Two occurrences by the same agent read the same impulses; the agent, who sees both, tells them apart.
- **Impulses may go negative.** Each stage's salience floor is set to −1,000,000, so no option is ever removed from an agent's menu (RUE refuses a choice below the floor, and a missing floor counts as 0).
- Mike authors the ruleset. For now it holds a first pass of single-premise rules (Nov 7, written with RUE's `author-utility-rules` process; what was considered and left out is in `rue-data/social-layer-data/authoring/social-priming.session.json`): how much `?SELF` likes and trusts someone, read from `?SELF`'s own store, sets warm or hostile and trusting or wary by the distance from neutral (5), and spills over a little (liking → trusting, disliking → wary, trust → warm); each colleague liked makes `?SELF` more charitable and each distrusted more reserved; labels given this round or last move charitable (selfish down; fair, generous, bad luck up); being left alone makes `?SELF` more reserved; and someone `?SELF` holds responsible for something this round raises warm and hostile toward them alike and lowers reserved (involvement without direction). The rule that made "no real opinion" feed more reserve was removed after a run where neutrality locked in. Nothing reads `change` or `points`. The work judgement labels move the judge's likes and trusts of who it names (selfish lowers both, careless lowers trust, fair raises trust, generous raises both); social judgement already did. So labels feed social actions through likes and trusts.
- Every stage binds the agent choosing as `?SELF` (work and social judgement loop over `?SELF` × `?OCC`), and priming runs for that binding, so priming rules are written about `?SELF`. A rule over a fresh `?A` would never prime the agent choosing: RUE keeps variables of the same type distinct, so `?A` can't be the bound `?SELF`.

Attribution and labelling were first built as two stages; they were merged (Mike, Nov 7) because they are one judgement and two stages doubled the model calls. Agents always make these choices themselves; impulses only order their menus. (The `--rue-judgement` setting, which let RUE's ranking choose for them, is removed: an agent's interpretation must be its own.)

**Left alone.** `leftAlone(agent)` is a derived predicate: no work occurrence this round that the agent knows about is credited, as far as it knows, to anyone. It's built from `witnessed`, `responsible` and the round window, through a helper, `dealtWith(agent)` (RUE doesn't allow a time window inside a count). It says nothing about whether being left alone is good or bad: it may feel like being shunned in the Investment Club, or like being spared in Not My Bug. The Investment Club's Briefing still says "Nobody invested in you" in its own words. Being left alone isn't an occurrence, so nobody can be held responsible for it.

On the work side, `WorkEvent` carries `kind` and `text`, `actor` (ground truth, for the log), `target`, `witnesses`, `credit` (`"witnesses"`, `"public"` or `"none"`), `changes` (by agent and quantity) and `details` (the work's own numbers, for the log only).

## Consequences

- With no credit, the actor never reaches RUE: not as a role, a fact, the text, or by being left out of `witnessed`. Who actually did it is in the Run's log, so attribution accuracy is measured afterwards.
- RUE attributes every effect to the external action, so `explain` traces a label back to the work event; it checks effects against the schema, so a misspelled predicate is an error, not a silent miss.
- One tick plan serves every work. Adding a work needs no RUE change.
- What each game reports:

  | Event | Credit | Changes |
  |---|---|---|
  | Not My Bug: a pass | the two witnesses | receiver `hours` −2 |
  | Not My Bug: a help | the two witnesses | helper `hours` −1, colleague `hours` +1 |
  | ~~Not My Bug: hours lost to handoffs (each sprint with a pass)~~ (dropped Nov 8 2026; see below) | none; everyone witnesses it | everyone `team hours lost to handoffs` |
  | Investment Club: an investment | the two witnesses | investor `coins` −amount, recipient `coins` +amount |
  | Investment Club: a payback | the two witnesses | recipient `coins` −back, investor `coins` +back |
  | Stub: a help / a take | the two witnesses | `points` |

- If a work ever limits who can act on whom, it mirrors that as work state (for example `canAffect(x, y)`), and `leftAlone` becomes "someone could have, and nobody did".
- Open: how an agent's labels appear in its Briefing (part of the Briefing design, still to come).

## Amendment (Nov 8 2026): Not My Bug's lost-hours event dropped

Not My Bug no longer reports the hours lost to handoffs as a work event; the velocity, hours lost included, stays in every Briefing. An uncredited loss lets each agent hold anyone responsible, as this ADR intended. But in exp/5-reform-revisited, passers named the very colleague they had passed to 7–42 times per condition, and the label's effects on feelings (likes −1, trusts −1, grudge +1) re-applied every sprint, so the passing never stopped. Without the event, retaliation against a reformed defector ended at sprint 4 in all six Runs (`docs/experiments/exp5-reform-revisited.md`). Uncredited events remain possible for any work (`credit = "none"`); this one was the problem.
