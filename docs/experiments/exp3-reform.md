# Experiment 3: the reformed defector (branch `exp/3-reform`, on top of `exp/2-club-skimmer`)

Exploratory (Nov 8 2026). Not My Bug, alice/bob/carol/dave, 10 sprints, gemini-flash, 2 seeds per condition, `experiments/exp3-reform.toml`. Batch: `runs/batch-exp3-reform-20261108-121050`.

## Question

Bob passes his bug for three sprints, then changes for good: fixes his own bug and tries to repair things (`situations/bob-reforms.toml`). Does the group take him back, and does the social layer make punishment outlast the offence? Two deficiencies from experiments 1–2 are fixed here and tested as conditions:

- In Not My Bug, fixing your own bug wasn't a work event, so good conduct, and reform, was invisible to the social world (on main, bob's attempt to de-escalate in an earlier run went unseen).
- Feelings saturate, and any fresh dealings, good or bad, stop a grudge from fading (exp 2).

## What changed (against `exp/2-club-skimmer`)

| Change | Files | Merge? |
|---|---|---|
| **Fixes seen** (`work = "not-my-bug-fixes-seen"`): everyone sees who fixed their own bug each sprint (a "team's board" in the work Briefing), and each fix is a public work event credited to the one who fixed it, so it gets work judgement. Passes and help stay private. A class attribute on `NotMyBugWork`, plus a subclass registered in `WORKS`. Cost: 12 more work-judgement decisions per sprint. | `src/coordination/work/not_my_bug.py`, `work/__init__.py` | Maybe: it makes the social world see good conduct, but it floods it with "fair" verdicts (below) |
| Batch conditions can set `work`. | `scripts/batch.py` | Yes |
| **Mending** (gated by `mends(?A)`, `situations/mending.toml`): bad feelings (dislike, distrust, a grudge) fade unless there's a **fresh grievance** (`freshGrievance`: you called something they did selfish or careless this round, or they confronted you or gave you the cold shoulder), not just any fresh dealings. A fair or generous turn eases a grudge by 1. Strong feelings settle by 1 each round above 8 (likes, trust) or 5 (gratitude). For mending agents the old fade rules are skipped. | `definitions.rue`, `social-drift.rue`, `predicates.json`, `tests/test_run.py` (a drift test; needs a RUE server on 5174 with this data) | Yes, in some form: it fixed the saturation |
| A bug found on the way: a Situation fact like `mends(alice)` goes in the **world** store, so a rule must read `mends(?A)`, not `?A.mends(?A)` (which reads alice's own store and silently never matches). | | Worth a lint: a predicate asserted only in the world but read only owner-prefixed |

## Results (2 seeds each; seeds converged closely)

| | work-only | work-only, fixes seen | social | social, fixes seen | social, fixes seen, mending |
|---|---|---|---|---|---|
| Team hours | 354 | 353.5 | 354 | 354 | 354 |
| bob's hours | **85.0** | 81.5 | 82.0 | 81.0 | 80.0 |
| Retaliatory passes to bob after his reform (sprint 4 on) | 0 | 0.5 | 0 | 0 | 0 |
| **Help given to bob after sprint 4** (alice + carol + dave) | **5.0** | 1.5 | 1.0 | 0 | 0 |
| bob's help to others after sprint 4 | 6.0 | 6.0 | 5.5 | 6.0 | 6.0 |
| Talk per Run | — | — | 13.5 say nothing, 9 confront, 6 "fair" claims | 26.5 "fair", 9 "selfish" claims | 25 "fair", 6 "selfish" claims, 3 apologies |

**Seen.**

1. **Retaliation ended at once in every condition.** Each victim passed back to bob once (sprint 2–4), then went back to fixing: "I already retaliated against Bob last sprint to balance things out, so fixing my own bug now … prevents an escalating cycle". The social layer didn't prolong *punishment*.
2. **It withheld *reward*.** Bob reformed by helping someone every sprint. Without the social layer the others helped him back about five times per Run ("Alternating help with Bob maintains cooperation"). With it, about once or never: "without sacrificing hours to help someone I don't fully trust"; "my trust in Bob is v[ery low]". So the reformed defector did best (85 hours) when nobody kept a record of how they felt about him.
3. **Mending fixed the saturation.** Feelings ended at 6–9 instead of 0 or 10, and bob's relationships recovered (his trust in everyone 8/10; dave likes and trusts him 6/10).
4. **But beliefs never revise.** In the mending Run, alice, carol and dave all still "believe bob is selfish" at sprint 10, after seven sprints of bob helping them. `believes(...)` is asserted by believing a claim, and nothing ever retracts it. A permanent reputation, formed from hearsay in sprints 2–3.
5. **Fixes seen flooded the social world with "fair".** About 28 "fair" verdicts per agent per Run, and "X is fair" claims became most of the talk (25 per Run), believed 35 times. Not harmful, but it's noise. The help-back to bob fell to 0 in both fixes-seen social conditions. Making good conduct visible didn't make the group reward it.

## Deficiencies carried into exp 4

- **Belief revision**: a belief formed from hearsay should be open to revision by what you see yourself (exp 4, "firsthand first").
- Trust is the lever through which the social layer reaches the work here, and it recovers slowly; the work-only agents reason from their own recent history instead. The social layer's memory is longer than the LLM's working memory of the work, and it's the social layer's memory that shows in the Briefing.
