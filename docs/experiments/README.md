# Experiments, Nov 8 2026 (exploratory, not findings)

Experiments run one after another, each on its own branch, each **stacked on the one before**, so that what one showed could be fixed before the next: `main` → `exp/1-testimony` → `exp/2-club-skimmer` → `exp/3-reform` → `exp/4-firsthand` → `exp/5-reform-revisited` → `exp/6-hearsay` → `exp/7-defector`. **Which changes to bring to main: [merge-candidates.md](merge-candidates.md).** Every experiment ran the same setup with no social layer (`social = "off"`) beside the social conditions. gemini-flash for every agent in exps 1–5 and gemini-flash-lite in exps 6–7 (flash hit its daily cap); 2–3 seeds per condition. Treat everything as observations, not findings.

| # | Branch | Question | What the social layer did | Write-up |
|---|---|---|---|---|
| 1 | `exp/1-testimony` | Bob dumps bugs only on dave (Not My Bug). Can talk get that to the bystanders? Adds **testimony** (tell someone what someone did). | **Nothing to the work.** Testimony did carry the information, but both parties testified, the listener doubted both, and doubting eroded her trust in both. Bystanders never act on it: the only move that touches bob is passing to him, which they won't do unprovoked. | [exp1-testimony.md](exp1-testimony.md) |
| 2 | `exp/2-club-skimmer` | Bob skims his investors (Investment Club). Does talk stop people investing in him sooner? | **Improved coordination**: praise kept everyone investing (+70 team coins, 3 of 3 seeds). Shunning bob needed no social layer (his one victim learned firsthand). Testimony crowded out praise and cost coins. The skimmer got a good name ("bob is generous") from his investing. | [exp2-club-skimmer.md](exp2-club-skimmer.md) |
| 3 | `exp/3-reform` | Bob defects for three sprints, then reforms. Does the group take him back? Adds **fixes seen** (work) and **mending** (RUE). | **Withheld reward**: retaliation ended at once in every condition, but without the social layer the others helped the reformed bob back about 5 times per Run; with it, 0–1 times ("someone I don't fully trust"). Mending fixed saturation, but "bob is selfish" beliefs never revised. | [exp3-reform.md](exp3-reform.md) |
| 4 | `exp/4-firsthand` | Bob smears an innocent dave (Club). Adds **firsthand first** (provenance, tier-2 priming, belief revision). | **Enabled exploitation**: dave lost about 70 of 200 coins with the social layer, and nobody invested in him. Firsthand first cut the loss by about a third where bystanders had dealings with dave, but a smear that isolates its target leaves nothing to revise against. | [exp4-firsthand.md](exp4-firsthand.md) |
| 5 | `exp/5-reform-revisited` | Exp 3 again, with firsthand first. Five batches (5–5e), each fixing what the last showed. | Found the **lost-hours blame loop**: passers blamed the colleague they'd passed to for the team's uncredited lost hours, the label's effects kept their feelings at 0, and they passed again (bob 60 hours). Without that event, retaliation ended at sprint 4, and the improved layer **rewarded reform** (4.3 helps back vs main's 1.7; bob 84.7 vs work-only 86). | [exp5-reform-revisited.md](exp5-reform-revisited.md) |
| 6 | `exp/6-hearsay` | The smear again, with **untested hearsay** (claims about someone you've never seen act count for less). On **gemini-flash-lite**. | Doubting rose (4.7 → 11.3 per Run), but only until the first contact with dave; alice believed the smear in all 9 social Runs. On flash-lite the smear didn't cost dave coins: a partner choice made before any talk mattered more. | [exp6-hearsay.md](exp6-hearsay.md) |
| 7 | `exp/7-defector` | A persistent defector against main's layer and the improved one, with and without the lost-hours event. On **gemini-flash-lite**. | bob passed half as often with a social world (4.7 vs 9.7), but his reasons misread the rules rather than fear sanctions: a confound from the social-life paragraph in his prompt, not from sanctions. The improved layer behaved like main's. | [exp7-defector.md](exp7-defector.md) |

**Then a preregistered confirmatory test of exp 2's observation (the Club's team coins), [prereg-confirmatory.md](prereg-confirmatory.md)** (tag `prereg-confirmatory-v1`), on gemini-3.6-flash and claude-haiku-5-5. **Results: [prereg-results.md](prereg-results.md).** Not supported on Gemini (+19 coins, p = 0.35); supported on Haiku (+323, p = 0.0004); the models differ (p = 0.001). On Haiku the gap starts before any talk, so the social-life paragraph and RUE's social world aren't yet separated.

**Model from here on: gemini-3.6-flash.** Experiments 1–5 used gemini-3.8-flash and 6–7 gemini-3.5-flash-lite, because 3.8 reached its daily cap (`docs/status.md`). Experiment files now default to `chooser = "gemini-3.6-flash"`; Runs record their model in `config.json` and in every decision.

## So far, what the social layer seems to do

- It **reaches the work only through partner choice** (whom to invest in, whom to help). In Not My Bug's pass/fix choice the models are cooperative unless hurt, whatever they hear.
- It **amplifies whatever the talk is about**: praise sustains investment (exp 2); a smear shuts its target out (exp 4); a past offence outlives the reform (exp 3).
- **Its memory outlasts the agents'**: work-only agents reason from recent sprints and forgive; the Briefing's social state keeps old distrust and permanent beliefs in front of them.
- **Grounding in RUE's record is a working defence** (exp 4), with a clear limit: it can weigh only what the agent saw.
- **It depends on the model** (exps 6–7): on flash-lite the smear didn't cost its target, victims barely retaliated, and the defector seemed confused by the social-life paragraph in his prompt. Results are per model.
- **Rules that read verdicts inherit the biases in how verdicts are made** (exp 5): self-serving blame for an uncredited loss became "firsthand evidence" until the rules required a credited actor.

## Changes worth considering for main

Most to least clear-cut:

1. Occurrence text in labels (`describe`, exp 1), colleague order shuffled per agent (exp 2), `work` as a batch condition key (exp 3), `scripts/analyze_exp.py` (exp 1).
2. Belief revision from firsthand verdicts, and `toldBy` provenance in the Briefing (exp 4).
3. Mending: grievances, not any dealings, keep bad feelings alive; strong feelings settle (exp 3).
4. Tier-2 priming from the agent's own verdicts (exp 4), for Mike's review.
5. Testimony (exp 1), if a work gives bystanders a lever; it needs a fix to doubt (repeated doubt drives trust to 0).
6. Fixes seen (exp 3): makes good conduct visible, but floods the social world with "fair".

The features are gated by Situation facts (`canTestify`, `mends`, `weighsFirsthand`) so each condition could switch them on and off. On main they'd become the default, and the gates and twin actions would go.

## Authoring lessons (RUE)

- Variables bound in a precondition aren't kept distinct; write `?A != ?B` (exp 1).
- A Situation fact without an owner goes in the world store; reading it as `?A.fact(?A)` silently never matches (exp 3).
- RUE renders an occurrence-typed role as its id; the harness substitutes the text (exp 1).
- `tests/test_run.py::test_mending_settles_strong_feelings_and_fades_grudges` needs a RUE server on 5174 serving this data. It fails against the authoring-tool server that was running (started 00:52, older data).
