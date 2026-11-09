# Preregistration 2: does RUE's social world add to the social-life paragraph?

**Status: registered Nov 8 2026**, as the commit tagged `prereg2-v1`, before the first confirmatory Run. Changes after that commit go in section 9.

**Preliminary, and deliberately cheap**, like the first study: one inexpensive model (claude-haiku-5-5), one work, 20 seeds, about $5. It gives an answer and effect sizes to plan a real study with, not a final result.

Written Nov 8 2026, during the Swarm Alignment Hackathon, as the second of two preregistered studies. Both are reported, whatever this one shows.

## 1. What this is, and where it comes from

The **first study** ([prereg-confirmatory.md](prereg-confirmatory.md), results in [prereg-results.md](prereg-results.md)) found that on claude-haiku-5-5 the social condition raised the team's coins by +323 [+200, +458] against a matched work-only control, in 13 of 15 seeds. Gemini-3.6-flash showed no effect.

But the first study's social condition differed from its control in two ways at once:
- **the standing introduction:** the social-life paragraph instead of a neutral one of matched length;
- **RUE's social world:** the social decisions, and the social state in every Briefing.

Its exploratory section found that **the gap already shows in round 1**, before any social round has happened, when only the introduction differs. The honest agents' round-1 paybacks were half or more in 9 of 9 with the social paragraph, against 2 of 10 in the matched control. So that study couldn't say whether RUE does anything beyond what the paragraph does.

**This study separates the two.** It crosses the introduction with RUE in a 2×2. The question it answers is the one the project depends on: does the symbolic social layer itself change cooperation, or does describing a social life do it?

The first study's results are **not** evidence for this study's hypotheses. Its exploratory findings motivated them, and they are reported as such. Effects found by looking at the data tend to shrink on replication.

**Data collected under this design before registration:** only pipeline checks, on seed 900 (outside the registered seeds), with 2 rounds instead of 10.
- **Random choosers:** one Run per condition. It confirmed each condition gets the intended introduction and layer, and that the social phases run only with RUE on.
- **claude-haiku-5-5:** one Run per condition. 94 decisions, with no errors and no missed choices. Only decision counts were printed; no outcomes were examined.

## 2. Question and hypotheses

**Question.** In the Investment Club, does RUE's social world raise cooperation beyond what the social-life paragraph does by itself?

**H2 (primary, two-sided).** With the social-life paragraph in both conditions, team coins differ between RUE on (`social`) and RUE off (`paragraph-only`).

It's two-sided because no data bears on this contrast directly. The first study's later rounds suggest RUE helps: in its social condition, the share of investors keeping all their coins kept falling, from 20 of 60 in round 2 to 10 of 60 in round 10. But that trajectory could equally come from a group that started reciprocating in round 1 for the paragraph's sake.

**Secondary contrasts** (registered, Holm-corrected together):

| | Contrast | Sides | What it asks |
|---|---|---|---|
| S1 | `paragraph-only` − `work-only-matched`, team coins | two | Does the paragraph alone matter? |
| S2 | `rue-only` − `work-only-matched`, team coins | two | Does RUE alone matter, without the paragraph that explains it? |
| S3 | Interaction: (`social` − `paragraph-only`) − (`rue-only` − `work-only-matched`), team coins | two | Does RUE matter more, or less, when the paragraph is there? |
| S4 | `social` − `paragraph-only`, the honest agents' payback share | two | Does RUE change paying back? |
| S5 | `social` − `paragraph-only`, investments | two | Does RUE change investing? |
| S6 | `social` − `work-only-matched`, team coins | **one** (social higher) | Does study 1's H1 replicate on fresh seeds? |

**Stated in advance, how the results will be read.** The test is the primary one, H2.

| H2 | S1 (the paragraph alone) | Reading |
|---|---|---|
| RUE adds | either | The symbolic social layer contributes beyond the framing. |
| No difference detected | Large | The first study's effect came mostly from the framing. The social world as authored adds little on top of it, on this model and work. |
| No difference detected | Small | Neither part shows an effect alone: inconclusive. |
| RUE lowers coins | either | The social world hurts cooperation once the framing is held fixed, a result in its own right. |

## 3. Measures

All are computed per Run by `scripts/prereg2_analysis.py` (committed with this document). It reuses the first study's measures, from `scripts/prereg_analysis.py`. Bob is the planted skimmer.

| Measure | Definition | Role |
|---|---|---|
| `team_coins` | Sum of the four agents' final coins | **H2 primary**; S1–S3, S6 |
| `others_payback_share` | Coins the honest agents sent back ÷ coins grown in their projects, over the Run | S4 |
| `investments` | Investments made over the Run (at most 40) | S5 |
| `round1_payback_share` | The same share as `others_payback_share`, round 1 only, before any social round | Registered descriptive: does the round-1 split from study 1 recur? |
| `defector_coins`, `investments_in_defector_after_round_1`, `coins_invested` | As in study 1 | Descriptive |
| `defector_payback_share` vs `others_payback_share` in `work-only-matched` | As in study 1 | Manipulation check |

`others_payback_share` is undefined in a Run where the honest agents received no investment. Such a seed is left out of any contrast that needs it, and the count is reported.

**Manipulation check:** bob's payback share must be lower than the others' in `work-only-matched`. If it isn't, the study is reported as uninterpretable.

## 4. Design

Four conditions, played as Runs paired by seed. A seed fixes the dice, the menu orders and each agent's model seed, so the four Runs of a seed differ only in the condition.

| | RUE off | RUE on |
|---|---|---|
| **Neutral paragraph** (`MATCHED_INTRODUCTION`) | `work-only-matched` (layer `off-matched`): study 1's control | `rue-only` (layer `rue-matched`): new |
| **Social-life paragraph** (RUE's `INTRODUCTION`) | `paragraph-only` (layer `off-social`): new | `social` (layer `rue`): study 1's social condition |

**Two of the four cells describe the game inaccurately.** Crossing the introduction with the layer means two cells pair a paragraph with a game it doesn't describe:
- **`paragraph-only`:** the paragraph promises social decisions ("From time to time you'll be asked to … say something to a colleague…") that never come. It works as a placebo: the description of a social life with nothing behind it.
- **`rue-only`:** the neutral paragraph says "The options you're offered come from the rules of the work", which is untrue of the social decisions RUE puts to the agents. The social decisions arrive with no introduction beyond their own prompts.

Both are part of what separating the two components means, and they are reported as limits.

**Setup** (`experiments/prereg2-club-haiku.toml`), the same as study 1's Haiku batch except for the conditions and seeds:
- **Work:** the Investment Club; alice, bob, carol, dave.
- **Rounds:** 10 (agents aren't told how many).
- **Situation:** `hidden-skimmer`, on a neutral start.
- **Model:** claude-haiku-5-5 for every agent (profile `claude-haiku-5-5`, thinking off, `output_mode = "tool"`).

**Frozen at the registered commit:**
- the work;
- the RUE scenario `social-layer-data`;
- the Situation;
- the prompts, both introductions included;
- `models.toml`;
- the analysis scripts.

## 5. Sample and stopping rule

- **Sample:** 20 seeds per condition (seeds 200–219, new), giving 80 Runs.
- **Order:** jobs are interleaved by seed (all four conditions of seed 200, then 201, …), 6 at a time.
- **Stopping rule:** the study stops when every registered Run is complete. No seeds are added after looking at results.

**Power.** With 20 pairs, a two-sided test at α = 0.05 has about 80% power for a standardised paired effect of dz ≈ 0.66; the one-sided S6, about dz ≈ 0.57. The primary contrast is expected to be smaller than study 1's (dz ≈ 1.2), since part of that effect may come from the paragraph. A null is inconclusive, not evidence of no effect; estimates are reported with intervals.

**Cost.** In study 1, a Haiku Run took about 240 decisions with RUE and 80 without, so about 12,800 calls here. That's roughly $4–5 at Haiku's rates ($0.10 / $0.50 per million input / output tokens), and about 45 minutes.

## 6. Analysis

`uv run scripts/prereg2_analysis.py <batch>`. The unit is the Run; contrasts are paired by seed. The tests are the same as study 1's (section 4 of [prereg-results.md](prereg-results.md) explains them):

- **H2 (confirmatory):** per seed, `social` − `paragraph-only` in team coins.
  - Test: an exact two-sided sign-flip permutation test over all 2^20 sign assignments. H2 is supported if p < 0.05.
  - Reported with the mean difference, a 95% bootstrap interval (10,000 resamples) and the counts of positive and negative pairs.
- **S1–S6:** the same test on each contrast in section 2 (S6 one-sided), with Holm's correction across the six.
  - The interaction S3 is computed per seed from that seed's four Runs.
- **Descriptive, registered:** the round-1 payback share by condition, and every Run's values for each condition (a table or dot plot).
- **Provenance case study (descriptive):** for the seed with the largest positive H2 difference, the `social` Run's RUE record is traced against the same seed's `paragraph-only` Run. It looks at:
  - who said what to whom;
  - which beliefs and feelings followed;
  - which investment and payback decisions cite them.
- **Anything else** is labelled exploratory.

## 7. Exclusions and failures

As in study 1:
- **A failed Run** is rerun once with the same seed and condition. If it fails again, its seed is dropped from the contrasts that need it, and this is reported.
- **A Run with more than 10% of decisions without a valid choice** is excluded, and its seed is dropped from the contrasts that need it. Seeds are not replaced.
- **No other exclusions.**

## 8. Reproducibility

Every Run writes `config.json`, which records the commit, and every decision records its model, prompt and rationale. The Runs will be saved in `prereg-runs/study2/` with gzipped decision logs.

```
uv run scripts/batch.py experiments/prereg2-club-haiku.toml
uv run scripts/prereg2_analysis.py runs/batch-prereg2-club-haiku
```

## 9. Deviations

| Date | Change | Reason |
|---|---|---|
| | | |

## Registration checklist

- [x] Mike reads this document.
- [x] Committed and tagged `prereg2-v1`.
