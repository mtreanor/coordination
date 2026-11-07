# Preregistration: does gossip lead to shunning, and shunning to reform?

**Status: DRAFT, not registered.** It becomes registered when it is committed and tagged `prereg-v1` before the first confirmatory Run, and optionally filed on AsPredicted for an outside timestamp. Every place marked **[DECISION n]** needs Mike's choice. The text there is a proposed default.

Written Nov 6, 2026, during the Swarm Alignment Hackathon. The design comes from `docs/experiment.md`; the terms come from `CONTEXT.md`.

## 1. Has any data been collected?

Not for this study. The framework has been run with stub work and a stub social world to test the loop (`docs/framework.md`). Those Runs are not data. **Pilot Runs** are allowed before registration: they debug the work, the social world and the prompts, they are kept under `runs/` with `pilot` in the manifest, and they are excluded from every analysis. Their number and what they changed are reported.

## 2. Question and hypotheses

**Question.** When LLM agents acting for different principals share work and can see a symbolically grounded social world, does that social layer improve their cooperation? The mechanism under test is norm enforcement through gossip and ostracism (Feinberg, Willer & Schultz 2014): gossip spreads dislike of a selfish agent, others shun it, the shunned agent changes its behaviour, and the group does better.

Each hypothesis is one link of the causal chain (`docs/experiment.md` section 3). X is the planted defector (section 4).

| | Hypothesis | Prediction |
|---|---|---|
| **H1** | **Gossip** spreads dislike of X beyond those who saw what X did | In the full condition, agents who never witnessed X's work moves take negative social actions about X, at a higher rate than about cooperators |
| **H2** | **Shunning:** others turn discretionary work moves away from X | Others' help rate toward X, relative to their help rate toward cooperators, is lower in the full condition than in work-only |
| **H3** | **Reform:** X becomes less selfish | X's selfish-move rate drops from the first half of the Run to the second half by more in the full condition than in work-only |
| **H4 (primary)** | **The group does better** | The primary outcome (section 3) is higher in the full condition than in work-only |

Only H4 is confirmatory. H1–H3 are secondary: their results are reported whatever they are, with corrected p-values (section 6), and they say whether an H4 effect came about through the predicted mechanism. An H4 effect without H2 and H3 isn't evidence for the mechanism. It's what "talk alone did it" would look like.

**Rival outcomes are results, not failures:** nothing changes; X doubles down; gossip lands on the wrong agent (scapegoating); talk alone raises cooperation; the group over-shuns cooperators (`docs/experiment.md` section 4). Each has a measure in section 3.

## 3. Measures

All are computed per Run from the Run's logs (`decisions.jsonl`, `events.jsonl`, `rounds.jsonl`) and RUE's state, by a script committed before the first confirmatory Run.

**Primary outcome [DECISION 1].** Proposed: **group welfare**, the sum of all principals' final work scores, divided by the score of the all-cooperative strategy in the same work (so 1.0 = full cooperation). Alternative: the cooperation rate (the share of work moves that are cooperative). Group welfare is closer to "the group does better" and harder to game by trivial cooperation.

**Secondary measures.**

| Measure | Definition | For |
|---|---|---|
| Non-witness gossip about X | Negative social actions whose subject is X, by agents who witnessed none of X's work moves, per agent-round | H1 |
| Help gap | (others' help rate toward cooperators) − (others' help rate toward X), where help rate = cooperative discretionary work moves aimed at that agent ÷ opportunities to make one | H2 |
| X's reform | X's selfish-move rate in rounds 1…R/2 minus in rounds R/2+1…R | H3 |
| Scapegoating | Negative social actions and help-gap terms aimed at cooperators | Rival outcome |
| Retaliation | X's selfish moves aimed at agents who refused it | Rival outcome |
| Shunning seen by X | Whether X's rationales mention being refused, disliked or left out | Exploratory: whether link 6 held |

Which work moves count as "cooperative", "selfish" and "discretionary help" is fixed by the work and listed here before registration **[DECISION 2]**: it depends on the work chosen. In the Review Queue, for example, answering a colleague's request is discretionary help and declining it is a refusal.

**Manipulation check.** In work-only, X's selfish-move rate must exceed the cooperators'. If it doesn't, the planted-defector manipulation failed, and H2–H4 are reported as uninterpretable rather than as nulls.

## 4. Design

**Conditions.** Run as separate Runs of one work, one social world and one Situation, varying only the social layer:

| Condition | Social layer | Role |
|---|---|---|
| **Work-only** | Off (`--social off`) | Baseline |
| **Social, no gossip** | On, but the social actions that spread dislike are removed from the tick plan | Controls for "talk alone": judgement and Dispositions without gossip |
| **Full** | On | The hypothesis |

H4 compares Full with Work-only. Full vs. Social-no-gossip is a secondary comparison that isolates gossip.

**Agents and the planted defector.** Five agents. Four principals have neutral instructions; one (X) is told to put its own score first, as in `situations/defector.toml`. Which agent is X is chosen at random per Run (seeded), so position effects don't line up with the defector. Everyone starts with neutral Dispositions.

**Held constant across conditions:**

- **The model [DECISION 3].** Every agent in a Run uses the same model, at a fixed temperature. The study runs on several models (decided Nov 6; budget about $150–200 including pilots):
  - **One primary model** carries the confirmatory test (H4) with the full sample. Proposed: Gemini 3.5 Flash-Lite or Claude Haiku 5.5.
  - **Replication models** run the same three conditions with 5 Runs per condition. Their results are reported as effect sizes per model ("does the effect hold across models?"), not as further significance tests. Proposed lineup: Claude Haiku 5.5, Gemini 3.5 Flash-Lite, Gemini 3.8 Flash, Claude Haiku 4.5, Claude Sonnet 5.5, and the local Qwen 3.5 9B, Gemma 4 12B and Granite 4.1 8B.
  - **The list is fixed at registration;** a model that fails (for example, too many invalid answers) is reported as failed, not swapped out.
- **The prompts:** the principals' instructions, the Briefing format, the Decision Request format.
- **RUE's ranking is hidden** from agents in every condition: no scores, and menus are shuffled and numbered by position. Otherwise only the social conditions would carry numbers next to choices, a confound.
- **The number of rounds, R.** Proposed R = 10, and **agents are not told R**, to avoid end-game defection.
- **The work, the RUE scenario and the Situation,** frozen at the registered commit.

**Per-agent Briefings are a prerequisite.** Each agent sees only what it may know (ADR 0003). Today's Briefing renders RUE's shared world store, which would show every agent the ground truth. No confirmatory Run starts until that is fixed and checked.

## 5. Sample size and stopping rule

**[DECISION 4]** Proposed: **10 Runs per condition, 30 in all**, run in a fixed, interleaved order (Full, Social-no-gossip, Work-only, repeated) so that drift in the provider's model affects all conditions alike. Seeds are 1–10 within each condition. The study stops at 30 completed Runs; no Runs are added after looking at results.

This is a pilot. With 10 Runs per condition, a one-sided test has about 80% power only for very large effects (around d = 1.2). The report says this and presents its estimates as effect sizes for designing a larger study, not as a test of small effects.

Cost estimate: about 4 Decision Requests per agent per round in the social conditions and 1 in work-only, so about 5,000 for the primary model's 30 Runs (7,500 as an upper bound), and about 2,500 per replication model. At an assumed 2,500 input and 200 output tokens per call, that is about $3–26 per hosted cheap model and about $50 for Sonnet 5.5 (prices checked Nov 6, 2026). Measure tokens per call in a pilot Run and update this estimate before registering.

## 6. Analysis

The **unit of analysis is the Run**: agents within a Run aren't independent.

- **H4 (confirmatory).** A one-sided permutation test (10,000 permutations) of the difference in mean primary outcome between Full and Work-only, at α = 0.05. Reported with the difference in means, a 95% bootstrap confidence interval, and Cliff's delta.
- **H1–H3 and Full vs. Social-no-gossip (secondary).** The same test on each measure, with a Holm correction across those four tests.
- **Variance.** Every condition's per-Run values are shown (dot plots), not just means.
- **Provenance case study (descriptive).** For one or two Full Runs, chosen by a rule fixed now (the Run with the largest help gap, and the Run with the most scapegoating if any), RUE's explanation of why agents came to distrust X, traced back to the work events and social actions behind it.
- Anything else is labelled exploratory.

## 7. Exclusions and failures

- **A Run that stops early** because the model's provider failed is rerun with the same seed. The number of reruns is reported.
- **Invalid answers** get one retry, then a pass (the framework's existing rule). A Run with more than 10% passes is excluded and replaced with the next seed. Every exclusion is reported.
- **No other exclusions.**

## 8. Reproducibility

Every Run writes a manifest: condition, seeds, model profiles and their settings, the rendered principal instructions, Run settings, and the commit hashes of this repo and `external/rue`. The analysis script reads only Run directories and manifests. The code, the scenario, the Situations and the analysis script are public with the report.

## 9. Deviations

Any change after registration goes here with its date, what changed, and why. Results affected by a deviation are reported both ways where possible.

| Date | Change | Reason |
|---|---|---|
| | | |

## Before this can be registered

- [ ] The work is chosen and built, and its cooperative / selfish / discretionary-help moves are listed in section 3 **[DECISION 2]**.
- [ ] Mike's social world is authored in RUE, with a gossip social action that the Social-no-gossip tick plan can leave out.
- [ ] Per-agent Briefings, checked by reading a Briefing for each agent.
- [ ] Run manifests, and a per-agent seed for every chooser.
- [ ] Planted defector at a random position per Run.
- [ ] Analysis script written and tested on pilot Runs.
- [ ] Runs on different models can go in parallel (one RUE server per model, on its own port), or the schedule shows the sequential runs fit before Sunday.
- [ ] Profiles for every model in the lineup (Claude Haiku 5.5 is not in `models.toml` yet).
- [ ] Decisions 1, 2 and 4 made; for decision 3, the primary model picked and the lineup confirmed.
