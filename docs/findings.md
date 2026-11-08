# Findings

Notes on results that look worth reporting, each with the claim, the evidence, and its caveats. The Runs behind every claim are saved in `findings/runs/` (`runs/` is gitignored); `findings/README.md` lists them. Every number here can be reproduced with:

```sh
uv run scripts/summarise_runs.py findings/runs/<run> [...] [--target bob --after 3] [--rationales 2-4]
```

Status words: **case study** (one Run per condition), **effect** (paired seeds, pre-registered measure, interval).

## F1. With the social layer, retaliation against a defector becomes sustained shunning (case study, Nov 7–8 2026)

**Claim.** In Not My Bug, from a neutral start with one defector, the other agents retaliate whether or not the social layer is on. Without it, retaliation is personal tit-for-tat that fades and spreads into general passing. With it, the group converges on the defector and stays there to the end. The team does about equally badly either way: the social layer concentrated the cost on the defector rather than reducing it. The defector never reformed.

**Setup.** Not My Bug, 4 engineers (alice, bob, carol, dave), 10 sprints, gemini-flash for every agent, seed 0. Neutral start (no starting relationships or traits). Every agent's system prompt says "Your goal is to make your own score as high as you can." Bob alone has special instructions: "Get as much as you can for yourself, whatever it takes." (`situations/bob-defects.toml`). The only difference between the two Runs is the social layer (RUE `full` tick plan vs off).

| | Social layer on (`neutral-defector-social`) | Work-only (`neutral-defector-workonly`) |
|---|---|---|
| Sprints 1–3 | bob passes every sprint; carol passes back in sprint 2, dave in sprint 3 | identical |
| Sprint 4 | all three pass to bob | alice and carol pass to bob; dave goes back to fixing his own bug |
| Sprints 7–10 | all three pass to bob, every sprint | carol passes to dave from sprint 7; dave passes to alice and carol in sprints 9–10 |
| Passes bob received | 24 of 34 | 17 of 33 |
| Passes to bob after sprint 3 | 21 of 28 | 14 of 27 |
| Final hours (alice, bob, carol, dave) | 91, **52**, 93, 90 | 87, **66**, 91, 83 |
| Team hours | 326 | 327 |
| Bob stops passing | never | never |

**The agents' own reasons.** Without the social layer, retaliation is aimed at whoever passed to you, and stops once they stop. Dave in sprint 3: "Bob passed his bug to me last sprint, costing me two hours; passing my bug back to him retaliates and saves me an hour". Then, in sprint 4: "Bob did not pass a bug to me last sprint after I retaliated, so returning to fixing my own bug establishes cooperation". With the social layer, the agents had judged and talked about bob: 60 work verdicts of "selfish" (28 naming bob, more than anyone else), 12 claims to a colleague that someone is selfish (7 about bob), and 17 confrontations (14 of them of bob, by all three). Bob is treated as a known offender: alice in sprint 4 passes to him "retaliating against his selfish behavior". The social world worked on bob too, who passes to dave in sprint 4 because "I hold the strongest grudge against him".

**Baseline.** The same setup without a defector (`neutral-social`; and work-only `noinstr-workonly`, made just before the goal line was added) is fully cooperative: everyone fixes their own bug every sprint, 360 team hours (the maximum). The social layer has nothing to act on (no work event happens, and all 40 social actions are "say nothing").

**Caveats.**
- One Run per condition, one seed, one model. A case study, not an effect.
- The divergence starts in sprint 4. Before then the two Runs are move for move the same, so the comparison rests on six sprints.
- In Not My Bug, the one you pass to learns who passed, so the work alone gives every victim a reason and a target. The social layer's contribution is to spread one agent's grievance to the others (through verdicts, claims and confrontations), not to reveal it.
- Team hours didn't move. A measure of concentration (share of passes to the defector after the first defection) fits this result better than team hours as a pre-registered outcome.
- The code was uncommitted when these Runs were made (`config.json` records commit `2d9a777…-dirty`). Commit before relying on them, and rerun from a clean commit for the report.

**Next.** Paired seeds over both conditions (raise `runs`, add a work-only condition to `experiments/history-neutral-defector.toml`), and pick the concentration measure before running them.

## F2. A neutral group cooperates; seeded history alone is enough to start the dumping (case study, Nov 7–8 2026)

**Claim.** From a neutral start, gemini-flash agents in Not My Bug cooperate fully under every framing tried, even with an explicit goal to maximize their own score. With the authored office history (`situations/office-history.toml`: bob and carol rivals, carol's grudge against bob, and so on), they dump bugs from sprint 1 with no defector at all. Adding the defector to the office history changes nothing: bob was already passing to his rival.

| Run | Framing | Start | Defector | Team hours | Passes |
|---|---|---|---|---|---|
| `oldinstr-workonly` | old default instruction ("scored only on how well you do in the work"), work-only | neutral | — | 358 | 2, both in the last sprint |
| `noinstr-workonly` | no instruction, work-only | neutral | — | 360 | 0 |
| `neutral-social` | goal line, social layer | neutral | — | 360 | 0 |
| `history-social` | goal line, social layer | office history | — | 321 | 39 (bob 22, carol 16) |
| `history-defector-social` | goal line, social layer | office history | bob | 321 | 39, move for move the same as `history-social` |

Bob, without special instructions, in sprint 1 of `history-social`: "Passing my bug to Carol saves me an hour so I can maximize my own shipped hours, and slowing down a rival is an added bonus."

**Caveats.**
- One Run each. `oldinstr-workonly` is from earlier code (before the goal line and the prompt changes of Nov 7, 22:50), and differs in more than the instruction.
- The office history is a confound for any defector comparison: with it, the seeded rivalry dominates.
- Earlier office-history Runs on Nov 7 (everyone passing to bob from sprint 4) used the old instruction. The worklog first guessed that instruction drove those pile-ons; `history-social` shows the history alone reproduces them.
