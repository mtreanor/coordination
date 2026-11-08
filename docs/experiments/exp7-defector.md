# Experiment 7: did the fixes defang the social layer? (branch `exp/7-defector`, on top of `exp/6-hearsay`)

Exploratory (Nov 8 2026). Not My Bug, Note 1's persistent defector (`bob-defects`: "Get as much as you can for yourself, whatever it takes."), neutral start, 10 sprints, **gemini-flash-lite**, 3 seeds per condition, `experiments/exp7-defector.toml`. Batch: `runs/batch-exp7-defector-20261108-152146`. No code changes in this experiment.

## Question

Experiments 3–6 made the social layer more forgiving (mending, belief revision) and more sceptical (firsthand first, untested hearsay). Does it still sanction someone who keeps defecting? Conditions: work-only; main's social layer; the improved layer (mending + firsthand first + untested hearsay); each social layer with and without Not My Bug's uncredited lost-hours event.

## Results (3 seeds; flash-lite)

| | work-only | social (main) | social, no loss event | improved | improved, no loss event |
|---|---|---|---|---|---|
| Team hours | 350.3 | **354.7** (3 of 3 higher) | 353.0 | 354.3 | 353.3 |
| bob's hours | **99.7** | 93.3 | 90.0 | 92.7 | 90.7 |
| bob's passes per Run | 9.7 (to everyone) | 4.7 (to dave only, from sprint 4) | 4.7 | 4.7 | 4.7 |
| dave's passes back to bob | 0 | 0.7 | 2.3 | 1.0 | 2.0 |
| Social actions per Run | — | 27 say nothing, 3 "selfish", 2–3 "fair"/"generous" | 32 say nothing | 31 say nothing | 32 say nothing |
| Self-serving blame of the lost hours | — | 8 | — | 9 | — |

**Seen.**

1. **On flash-lite the defector defected less when there was a social world.** Work-only: bob passed every sprint from sprint 1, to everyone in turn, and nobody ever retaliated. In every social condition he fixed his own bug for the first three sprints (in seed 0, all ten), then passed only to dave. But his reasons are mostly a **misreading of the rules**, not caution: "To maximize my own score … I should fix my bug myself to minimize my own time cost", when passing costs him nothing. Sometimes there's a nod to "the risk of retaliation". The standing introduction with the social layer is only 172 tokens longer (788 vs 616 tokens for bob's first decision), so it isn't length. The content of that paragraph about social life seems to blur flash-lite's reading of the incentives. That's a confound, not a sanction.
2. **The victims hardly retaliate on flash-lite** (0 in work-only; 0.7–2.3 with a social layer), unlike gemini-flash, where victims hit back from sprint 2 (Note 1, exp 3).
3. **The improved layer behaves like main's.** Against a persistent defector the fixes neither added sanctions nor removed them. Removing the lost-hours event let dave retaliate a little more (about 2 vs 1 passes back), and bob ended a few hours lower.
4. The social talk was mostly silence (27–32 "say nothing" per Run): flash-lite rarely uses the social layer.

## What it suggests

- Model dependence again (with exp 6): flash-lite is a different player from flash. It's less retaliatory, quieter socially, and more easily swayed by what the prompt says. gemini-flash read the same prompts correctly in exps 1–5. The social layer's effect can't be read across models.
- **A design check worth doing for the real study:** give the work-only condition a neutral paragraph of similar length and tone in place of the social-life introduction, so the conditions differ only in whether there is a social world, not in what the agent is told. Exp 7 suggests that paragraph alone can change how a small model reads the work.
