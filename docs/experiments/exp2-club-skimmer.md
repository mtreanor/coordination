# Experiment 2: the hidden skimmer in the Investment Club (branch `exp/2-club-skimmer`, on top of `exp/1-testimony`)

Exploratory (Nov 8 2026). Investment Club, alice/bob/carol/dave, 10 rounds, gemini-flash, 3 seeds per condition, `experiments/exp2-club-skimmer.toml`. Batch: `runs/batch-exp2-club-skimmer-20261108-114644`.

## Question

Experiment 1 showed that in Not My Bug the bystanders have no work move that acts on what they learn. The Club has one: whom you invest in. Bob sends back as little as he can to anyone who invests in him, and is otherwise a good colleague (`situations/hidden-skimmer.toml`). Only each investor knows what came back to it. Does the social layer, with or without testimony, get people to stop investing in bob sooner?

## What changed (against `exp/1-testimony`)

| Change | Files | Merge? |
|---|---|---|
| **Colleague order.** Each agent's colleagues are named in a seeded random order in its standing introduction, fixed for the Run (exp 1: 27 of 28 accounts went to the first-named colleague). `Run(..., seed=)`; `play.py` passes the config's seed. | `src/coordination/run.py`, `scripts/play.py`, `tests/test_run.py` | Yes |
| `situations/hidden-skimmer.toml`, `experiments/exp2-club-skimmer.toml` | | Optional |

## Results (3 seeds; the dice differ by seed, so compare within a seed)

| | work-only | social | social + testimony |
|---|---|---|---|
| Team coins by seed (0, 1, 2) | 1240, 840, 830 | **1290, 900, 930** | 1230, 800, 820 |
| Paired difference from work-only | | **+70 (3 of 3 higher)** | −20 (3 of 3 lower) |
| Investments per Run (of 40 possible) | 35 | **40** | 38 |
| Investments in bob after round 1 | 0.3 | 0 | 0 |
| bob's coins | 142 | 166 | 145 |
| Talk per Run | — | 24 "generous", 9 "fair", 2 "selfish" claims; 33 claims believed | 20 accounts, 6 "generous", 5 "fair", 4 "selfish"; 14 accounts taken in, 8 doubted |

**Seen.**

1. **Shunning bob needed no social layer.** In every Run alice invested in bob in round 1, got nothing back, and never invested in him again. Nobody else did either, in any condition. Partners lock in at round 1 (alice→carol, carol→alice, dave→alice or carol), so bob only ever had one victim, and she learned firsthand.
2. **The social layer raised investment, and with it the team's coins.** Without it, one agent in seeds 1 and 2 stopped investing from round 3 or 4. With it, everyone invested every round (40 of 40). The talk was overwhelmingly positive ("X is generous", believed 33 times per Run). This is the first sign of the social layer *improving* coordination: praise kept people investing.
3. **Testimony crowded the praise out.** Each agent gets one social action per round. With testimony, about half went on accounts ("alice sent back 20 coins to carol…") instead of praise. Investment fell back (38) and team coins fell below work-only in all three seeds.
4. **The skimmer got a good reputation.** In social seed 1, alice warned carol ("bob is selfish") in round 1, and carol doubted it (neutral trust). Then bob's own investments in others were labelled generous, and "bob is generous" spread from dave to carol and back, every round to the end. Alice herself said "bob is fair" by round 5. The labels are one-dimensional: they describe a person's character, not the role they played, so a generous investor can be a cheat as a trustee and the labels can't say so.
5. **Every feeling saturates.** By round 10 of social seed 0, alice likes and trusts everyone 10/10 and is 9–10/10 grateful to all three, bob included, though she still holds a 1/10 grudge against him. Each positive label or belief adds +1 to likes, trusts and gratitude every round, and drift is blocked whenever there are fresh dealings, which in the Club is every round.

## Deficiencies to fix next (carried into exp 3 and exp 4)

- Saturation and no recovery: label and belief effects stack without limit, and *any* fresh dealing (good or bad) stops drift. So grudges can't fade while you keep dealing with someone, even when the dealings are good. Fixed in exp 3 ("mending").
- One-dimensional labels: a natural next step is labels about the act ("kept most of it", "paid back fairly") rather than the person. Not attempted here.
- Hearsay against firsthand: a warning from someone you've no reason to trust is doubted, and praise from friends is believed even against your own experience. Addressed in exp 4 ("firsthand first").
- Talk budget: one social action per round means accounts compete with praise. Not changed.
