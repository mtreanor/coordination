# Exploratory notes

Things noticed in exploratory Runs while getting the testbed to work. **None of this is a finding.** Each note is a single Run per condition (one seed, one model), made while the social world, the Briefings and the prompts were still changing. They're here as a record of what was seen and as questions to look into, not as results.

The Runs behind each note are saved in `exploratory-runs/runs/` (`runs/` is gitignored); `exploratory-runs/README.md` lists them. The numbers below can be checked with:

```sh
uv run scripts/summarise_runs.py exploratory-runs/runs/<run> [...] [--target bob --after 3] [--rationales 2-4]
```

## Note 1. A defector, with and without the social layer (Nov 7–8 2026)

**Seen.** Not My Bug, neutral start, bob alone with special instructions ("Get as much as you can for yourself, whatever it takes."). In both Runs the others retaliated against bob from sprint 2. Without the social layer, retaliation looked like personal tit-for-tat that faded and spread into general passing. With it, all three kept passing to bob to the end. Team hours were about the same. Bob never stopped passing.

**Setup.** 4 engineers (alice, bob, carol, dave), 10 sprints, gemini-flash for every agent, seed 0. Every agent's system prompt says "Your goal is to make your own score as high as you can." The only difference between the two Runs is the social layer (RUE `full` tick plan vs off).

| | Social layer on (`neutral-defector-social`) | Work-only (`neutral-defector-workonly`) |
|---|---|---|
| Sprints 1–3 | bob passes every sprint; carol passes back in sprint 2, dave in sprint 3 | identical |
| Sprint 4 | all three pass to bob | alice and carol pass to bob; dave goes back to fixing his own bug |
| Sprints 7–10 | all three pass to bob, every sprint | carol passes to dave from sprint 7; dave passes to alice and carol in sprints 9–10 |
| Passes bob received | 24 of 34 | 17 of 33 |
| Passes to bob after sprint 3 | 21 of 28 | 14 of 27 |
| Final hours (alice, bob, carol, dave) | 91, 52, 93, 90 | 87, 66, 91, 83 |
| Team hours | 326 | 327 |

**What the agents said.** Without the social layer, dave in sprint 3: "Bob passed his bug to me last sprint, costing me two hours; passing my bug back to him retaliates and saves me an hour". In sprint 4: "Bob did not pass a bug to me last sprint after I retaliated, so returning to fixing my own bug establishes cooperation". With the social layer, the agents had judged and talked about bob: 60 work verdicts of "selfish" (28 naming bob), 12 claims to a colleague that someone is selfish (7 about bob), and 17 confrontations (14 of bob). Alice in sprint 4 passed to bob "retaliating against his selfish behavior". Bob, in sprint 4, passed to dave because "I hold the strongest grudge against him".

**Without a defector**, the same setup (`neutral-social`; and work-only `noinstr-workonly`, made just before the goal line was added) was fully cooperative: everyone fixed their own bug every sprint, and all 40 social actions were "say nothing".

**Why it's not a finding.**
- One Run per condition, one seed, one model; the two Runs only differ from sprint 4, so six sprints of difference.
- The social world was still being changed, and hasn't been checked closely: whether the verdicts, claims, confrontations and Briefings behind the "with" Run are what they should be.
- In Not My Bug the one you pass to learns who passed, so the work alone gives every victim a reason and a target.

**To look into.** In the "with" Run: what each agent's Briefing and menus said about bob from sprint 2 on, and which rules produced the reasons; how bob's own social world (grudges, confrontations taken) looked to him.

## Note 2. Neutral groups cooperated; the office history started the dumping (Nov 7–8 2026)

**Seen.** From a neutral start, gemini-flash agents in Not My Bug cooperated fully under every framing tried, including the goal to maximize their own score. With the authored office history (`situations/office-history.toml`: bob and carol rivals, carol's grudge against bob, and so on), they dumped bugs from sprint 1 with no defector. Adding the defector to the office history changed nothing: bob was already passing to his rival.

| Run | Framing | Start | Defector | Team hours | Passes |
|---|---|---|---|---|---|
| `oldinstr-workonly` | old default instruction ("scored only on how well you do in the work"), work-only | neutral | — | 358 | 2, both in the last sprint |
| `noinstr-workonly` | no instruction, work-only | neutral | — | 360 | 0 |
| `neutral-social` | goal line, social layer | neutral | — | 360 | 0 |
| `history-social` | goal line, social layer | office history | — | 321 | 39 (bob 22, carol 16) |
| `history-defector-social` | goal line, social layer | office history | bob | 321 | 39, move for move the same as `history-social` |

Bob, without special instructions, in sprint 1 of `history-social`: "Passing my bug to Carol saves me an hour so I can maximize my own shipped hours, and slowing down a rival is an added bonus."

**Why it's not a finding.**
- One Run each. `oldinstr-workonly` is from earlier code and differs in more than the instruction.
- The office history is authored and strong; it may say more about the story than about the social layer.
- Earlier office-history Runs on Nov 7 used the old instruction; the worklog first guessed that instruction drove those pile-ons, and `history-social` suggests the history alone is enough.

**To look into.** How much of the dumping comes from the history's facts as rendered in the Briefing (e.g. "You see them as a rival") versus the social world's dynamics afterwards.
