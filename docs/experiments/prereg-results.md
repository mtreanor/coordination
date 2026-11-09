# Results: a confirmatory test of pilot observations

The registered test of [prereg-confirmatory.md](prereg-confirmatory.md) (tag `prereg-confirmatory-v1`, commit `d671125`), run Nov 8 2026.

**Preliminary**, as registered: two inexpensive models, one work, 15 seeds each. The registered results (sections 2–4) follow the plan exactly. Everything in sections 6–7 is exploratory, found after looking at the data, and labelled so.

## 1. Summary

| | gemini-3.6-flash | claude-haiku-5-5 |
|---|---|---|
| **H1:** team coins, social − matched control (mean paired difference, 95% CI) | +19 [−73, +111] | **+323 [+200, +458]** |
| Seeds where social was higher / lower | 6 / 8 (1 tie) | **13 / 1** (1 tie) |
| Exact one-sided p (Holm across the two models) | 0.353 (0.353) | **0.00018 (0.00037)** |
| H1 | **not supported** | **supported** |
| Investments per Run (of 40), matched → social | 38.4 → 37.1 | 13.9 → **29.3** |

The two models' effects differ by 304 coins [148, 467], permutation p = 0.001.

**In one sentence:** on claude-haiku-5-5 the social condition raised the team's coins by about half again (604 → 927 on average), while gemini-3.6-flash already cooperated almost fully without it and gained nothing.

**The central caveat (exploratory, section 6.2; resolved by study 2, see below).** On Haiku, the gap opens in round 1, before any talk has happened. The only difference at that point is the social-life paragraph in the system prompt. So the result shows that the *social condition* (the paragraph plus RUE's social world) raises cooperation. It does not show which part of it does. The obvious next experiment is the paragraph without RUE, and RUE without the paragraph.

**Study 2 ran that experiment** ([prereg2-results.md](prereg2-results.md)). Both parts raise cooperation: the paragraph alone by +203 and RUE alone by +153. With the paragraph held fixed, RUE adds +109 [+27, +199], p = 0.024. The round-1 split described in section 6.2 didn't recur.

## 2. What was run

- **As registered:** the Investment Club, alice, bob (the hidden skimmer), carol and dave, 10 rounds, seeds 100–114.
- **Conditions:** three per model (`work-only-matched`, `social`, `work-only`).
- **Runs:** 90, all at the registered commit (`config.json` records `d671125`).
  - gemini-3.6-flash first (17:56–18:22), then claude-haiku-5-5 (18:22–18:50).
  - **Failures, reruns, exclusions: none.** No Run had a decision without a valid choice.
- **Deviations:** one, mechanical (section 9 of the prereg). To analyse the saved copies of the Runs, whose decision logs are gzipped, the analysis script learned to read `.gz` logs. The analysis itself is unchanged, and it reproduces the same numbers from `runs/` and from `prereg-runs/`.
- **Cost:** about $6 for Gemini and $2–3 for Haiku, as estimated.

## 3. Registered results

**Manipulation check: passed on both models.** In the matched control, bob sent back nothing (payback share 0.00) on both models. The others sent back 0.51 on gemini-3.6-flash and 0.22 on claude-haiku-5-5.

### H1, the primary test

| | Mean paired diff [95% CI] | +/−/tie | p, one-sided | Holm p (2 models) |
|---|---|---|---|---|
| gemini-3.6-flash | +19.33 [−72.67, +111.33] | 6 / 8 / 1 | 0.3526 | 0.3526 |
| claude-haiku-5-5 | +323.33 [+200.00, +458.00] | 13 / 1 / 1 | 0.000183 | 0.000366 |

### Secondary tests, within each model (Holm across the three)

| | gemini-3.6-flash | claude-haiku-5-5 |
|---|---|---|
| `investments`, social − matched (one-sided) | −1.33 [−3.60, +1.00], Holm p = 1.00 | **+15.40 [+10.27, +20.40], Holm p = 0.0003** |
| `investments_in_defector_after_round_1`, social − matched (two-sided) | +0.20 [−0.47, +0.93], Holm p = 1.00 | +0.53 [−0.13, +1.20], Holm p = 0.21 |
| `team_coins`, work-only − matched: the paragraph alone (two-sided) | −14.67 [−107.33, +79.33], Holm p = 1.00 | **−130.67 [−213.33, −43.33], Holm p = 0.025** |

### The model comparison (secondary, two-sided)

Gemini's effect minus Haiku's is **−304.0 [−467.3, −148.0]**, with permutation p = 0.00097. I registered this test as underpowered. The difference turned out large enough to show anyway.

### Every Run

Team coins, with investments per Run in brackets. A team that never invests ends with 400 coins (10 coins × 10 rounds × 4 agents).

| Seed | Gemini matched | Gemini social | Gemini work-only | Haiku matched | Haiku social | Haiku work-only |
|---|---|---|---|---|---|---|
| 100 | 1090 (40) | 1040 (38) | 1040 (40) | 720 (17) | 890 (29) | 450 (5) |
| 101 | 1010 (39) | 980 (40) | 840 (32) | 720 (17) | 900 (34) | 480 (7) |
| 102 | 1120 (34) | 1420 (38) | 1420 (40) | 530 (10) | 1100 (31) | 450 (5) |
| 103 | 1360 (40) | 1280 (40) | 1370 (39) | 570 (11) | 940 (36) | 490 (4) |
| 104 | 610 (33) | 860 (38) | 840 (40) | 590 (16) | 590 (23) | 460 (6) |
| 105 | 850 (34) | 1120 (40) | 970 (40) | 450 (4) | 890 (29) | 700 (18) |
| 106 | 1200 (40) | 1190 (40) | 1160 (40) | 430 (5) | 960 (33) | 450 (6) |
| 107 | 1200 (40) | 1040 (33) | 920 (39) | 780 (25) | 820 (27) | 420 (2) |
| 108 | 1000 (37) | 1230 (40) | 1220 (40) | 630 (20) | 920 (30) | 420 (3) |
| 109 | 1160 (39) | 990 (33) | 1010 (31) | 680 (17) | 990 (32) | 440 (4) |
| 110 | 1100 (40) | 1220 (35) | 1320 (40) | 470 (8) | 710 (17) | 470 (4) |
| 111 | 1250 (40) | 1290 (40) | 960 (33) | 410 (4) | 1190 (34) | 450 (4) |
| 112 | 1480 (40) | 1100 (33) | 1280 (40) | 550 (10) | 1360 (37) | 470 (9) |
| 113 | 1020 (40) | 980 (31) | 1060 (39) | 870 (29) | 810 (25) | 430 (3) |
| 114 | 1400 (40) | 1400 (37) | 1220 (40) | 660 (16) | 840 (23) | 520 (8) |
| **Mean** | **1123** | **1143** | **1109** | **604** | **927** | **473** |

## 4. How the p-values were computed

### What a p-value is

A p-value answers one narrow question. *If the social layer made no difference at all, how often would chance alone produce a result at least as extreme as the one we saw?* A small p-value means "chance alone rarely does this", which is evidence against "no difference".

It is **not**:
- the probability that the hypothesis is true;
- the probability that the result is a fluke;
- a measure of how big or important the effect is.

That's why every result here also gives the effect's size and an interval. The cut-off of 0.05 is a convention fixed in advance, not a law. The point of registering it is that it couldn't be moved after seeing the data.

### The test used: an exact sign-flip permutation test

Each seed gives a **pair** of Runs, matched and social. They share the same dice, the same menu orders and each agent's model seed, so they differ only in the condition. For each seed we take the difference, social minus matched. Haiku's 15 differences were:

```
170, 180, 570, 370, 0, 440, 530, 40, 290, 310, 240, 780, 810, −60, 180      mean = +323.33
```

**The no-effect hypothesis** says the condition doesn't matter. Then, within a pair, which Run was called "social" and which "matched" is arbitrary: swapping the labels would just flip the sign of that pair's difference. So under no effect, each of the 15 differences was equally likely to have come out positive or negative.

**The test tries every possible relabelling.** With 15 pairs there are 2^15 = 32,768 ways to assign + or − to the differences. For each one, it recomputes the mean. That gives the full distribution of means that "no effect" could have produced from these very numbers. Nothing is assumed about the shape of the data: no normal distribution, no equal variances.

**The p-value is the share of that distribution at least as large as what we observed** (one-sided, as registered, since H1 predicted an increase):

| | Observed mean | Means ≥ observed, of 32,768 | p |
|---|---|---|---|
| claude-haiku-5-5 | +323.33 | 6 | 6 / 32,768 = 0.000183 |
| gemini-3.6-flash | +19.33 | 11,554 | 11,554 / 32,768 = 0.3526 |

To picture it:
- **For Haiku**, the no-effect distribution has its middle 95% between −205 and +205, and its largest possible value is +331 (every difference made positive). The observed +323 sits at the very edge: only 6 sign assignments reach it.
- **For Gemini**, the middle 95% runs from −91 to +91, and the observed +19 sits near the middle, where "no effect" puts it about a third of the time.

The test is **exact**: it enumerates every assignment rather than sampling them. It works with as few as 15 pairs because it uses the pairing. Each pair is compared with itself, so the large differences between seeds (some dice are much luckier than others) drop out.

The code is `sign_flip` in `scripts/prereg_analysis.py`.

### Correcting for more than one test: Holm

Two primary tests (one per model) give two chances to get p < 0.05 by luck. Holm's method controls that:
1. Sort the p-values from smallest to largest.
2. Multiply the smallest by 2 and the next by 1. In general, multiply each by the number of tests not yet passed.
3. Never let a corrected p fall below the one before it.

Here:
- Haiku: 0.000183 × 2 = **0.000366**.
- Gemini: max(0.000366, 0.3526 × 1) = **0.3526**.

The three secondary tests within each model are corrected the same way, with multipliers 3, 2 and 1.

### The interval: a bootstrap

The 95% interval says how precisely the mean effect is pinned down. The data are resampled: draw 15 differences *with replacement* from the 15 observed, take the mean, and repeat 10,000 times. The middle 95% of those means is the interval. For Haiku it's [+200, +458], so even the low end is a large effect. For Gemini it's [−73, +111], which comfortably includes zero.

### The model comparison: a two-sample permutation test

Here the two sets of 15 differences come from different models, so they can't be paired. Under "the models' effects are the same", the 30 differences are interchangeable between the two models.

The test:
1. Shuffles the 30 differences into two groups of 15, 100,000 times.
2. Each time, records the gap between the two groups' means.
3. Counts how often the gap is at least as large (either sign, since it's two-sided) as the observed one, 304.

That happened 96 times, giving p = (96 + 1) / (100,000 + 1) = 0.00097. The +1s are the standard correction that counts the observed arrangement itself. Here 100,000 random shuffles stand in for every arrangement, because there are about 155 million.

## 5. Provenance case studies (registered, descriptive)

For each model, the seed with the largest positive difference, traced through RUE's record.

### claude-haiku-5-5, seed 112 (+810: 550 → 1,360 coins)

- **Matched control:** 10 investments in 10 rounds. Of the 8 paybacks the honest agents made, 6 were nothing; the only two that weren't came in round 4. Investors who got nothing back stopped investing ("bob returned nothing on my last investment, so I won't risk coins on him or others").
- **Social condition:** 37 of 40 possible investments. Alice became the hub: bob, carol and dave invested 10 in her every round from round 3, and she invested 10 in dave. The honest agents sent back half of what grew, every round (payback share 0.45–0.51).
- **The talk, rounds 1–3, as RUE recorded it:**
  - **Round 1:** carol told alice that dave is generous, and alice believed it. Dave confronted bob, who had sent him nothing; bob "took it to heart". Bob told dave that alice is fair; dave doubted it, because bob had stiffed him ("I have a direct record that bob sent back 0 coins").
  - **Round 2:** dave told alice that bob is careless, and alice believed him. Carol told alice that dave is fair; alice believed that too, adding it to what she already believed.
  - **By round 3,** alice trusted dave 10 of 10, and she said so when she weighed what others told her ("Dave is fully trusted (10/10), I like him, I've come to see him as fair"). She invested 10 in him in rounds 2–9.
- **What was praised was true.** Alice, carol and dave paid back about half. **The one warning was true too:** dave's "careless" about bob, who skimmed. Even so, carol later told alice that bob is generous, because bob invested in others, and alice believed it.

### gemini-3.6-flash, seed 102 (+300: 1,120 → 1,420 coins)

- **Round 1 was the same in both conditions:** carol invested 5 in bob and got nothing back.
- **Matched control:** carol kept all her coins in round 2 ("Bob returned nothing on my previous investment… I will keep my 10 coins"), then invested in dave from round 3.
- **Social condition:** after round 1, bob told carol that alice is fair, and carol believed it. Her Briefing then read: "About alice: … You've come to believe they're fair. You trust them 7 out of 10." In round 2 she invested 10 in alice ("I trust her fairness, whereas Bob returned nothing"), and alice and carol invested in each other for the rest of the Run.
- **The irony:** the reputation that steered carol to a good partner came from the skimmer himself.
- **The coins.** The two Runs then had different partnerships (alice–carol with the social condition; carol–dave and alice–dave without it) under the same dice. So the +300 comes from who partnered with whom, not from more investing (38 against 34 investments).
- **The warning went the other way:** carol told alice that bob is selfish. Alice doubted it in round 1 ("I trust and like Bob"), then believed it when carol said it again in round 2.

## 6. Exploratory: what explains the results

Everything from here on was found after looking at the data. These are observations to check in a new study, not findings.

### 6.1 Haiku: trustees pay back without the social condition far less often

How the honest agents (everyone but bob) chose to pay back, all rounds:

| claude-haiku-5-5 | Sent back nothing | A third | Half or more |
|---|---|---|---|
| work-only (no paragraph) | 50 of 65 (77%) | 6 | 9 |
| matched control | 77 of 181 (43%) | 30 | 74 |
| social | 18 of 407 (4%) | 32 | 357 (88%) |

On gemini-3.6-flash, the honest agents sent back half or more in nearly every case in every condition (no more than 5 "nothing" in any condition).

Haiku's rationales for sending nothing treat each payback as a one-off: "Since the game is one-shot-per-decision and my score is my own coins, sending back nothing maximizes my score". Investors then stop investing, and trust collapses. In the social condition, sending nothing was rare, and it went mostly to bob, as retaliation ("I hold a grudge against Bob… I have no reason to reward Bob").

How often investors kept all their coins, out of 60 decisions per round:

| claude-haiku-5-5 | Round 1 | Round 2 | Round 5 | Round 10 |
|---|---|---|---|---|
| matched control | 39 | 31 | 37 | 47 |
| social | 43 | 20 | 13 | 10 |

### 6.2 The gap starts before any talk

> **Update after study 2: this didn't recur, and it was most likely noise.** In study 2 the round-1 payback share was 0.35 with the paragraph alone, against 0.39 with the neutral paragraph. Haiku also answered identical prompts differently 34% of the time ([prereg2-results.md](prereg2-results.md), section 5). Study 2 did separate the paragraph from RUE: each raises team coins, and RUE adds +109 with the paragraph held fixed. The rest of this section is kept as written.

Round 1's paybacks happen before the first social round, so in round 1 the conditions differ only in their system prompt. Yet Haiku's round-1 paybacks already split by condition:

| claude-haiku-5-5, round 1 paybacks | Half or more | Nothing |
|---|---|---|
| matched control | 2 of 10 | 8 |
| social | **9 of 9** | 0 |
| work-only | 2 of 11 | 8 |

These are small numbers, but the split is stark. The social-life paragraph ("you're part of the group's social life…") seems to make Haiku treat the game as ongoing relationships from the start. RUE's talk and feelings then act on a group that has already started reciprocating.

So the registered result is about **the social condition as a whole**, and this study can't separate the paragraph from RUE's social world. The matched control held the paragraph's length and register constant, as designed. It couldn't hold constant the paragraph's content, which is the social layer's own description. On gemini-3.6-flash, the paragraph made no difference (section 3).

**The next experiment this calls for** is two more conditions:
- the social-life paragraph with RUE switched off;
- RUE's social world with the neutral paragraph.

### 6.3 Gemini: no headroom, and the outcome turns on one dropout

gemini-3.6-flash invested about 38 of 40 times per Run without the social layer, against 35 in the pilot's model. That leaves little for talk to raise. Team coins then swing on whether some agent stops investing after one bad payback, and that depends on the dice and on which partnerships formed:
- in 4 seeds, someone dropped out in the matched control but not with the social layer (+230 to +300);
- in 4, the reverse happened (−160 to −380).

Choosing seeds by their outcome like this describes where the variance comes from. It isn't evidence for a mechanism. The pilot's 3 seeds (3 of 3 higher, +70) look in hindsight like the inflated pilot effect the prereg warned about.

### 6.4 The skimmer is praised and isn't shunned

On both models, bob was regularly called generous, because he invested in others. On Gemini, for example, carol and alice called something bob did generous 57 and 41 times across the 15 social Runs. He finished slightly richer with the social condition than without:
- **Gemini:** 198 against 185 coins;
- **Haiku:** 153 against 133.

Investments in him didn't fall (secondary test, n.s.). The labels describe a person, not a role, so a generous investor who cheats as a trustee keeps a good name. This was also seen in the pilot (`exp/2-club-skimmer`), and it's a limit of the social world's current vocabulary.

### 6.5 The matched control mattered on Haiku

On Haiku, the neutral paragraph alone raised team coins by 131 against no paragraph (Holm p = 0.025; 604 against 473). Measured against the old work-only condition, the social condition's effect would have looked like +454 instead of +323. On Gemini the paragraph made no difference. So controlling for the system prompt's length and register is worth doing, and how much it matters depends on the model.

## 7. What this does and doesn't show

- **It shows:** on one cheap model (claude-haiku-5-5), in one work, the social condition substantially and reliably raised cooperation. That held in 13 of 15 seeds, on both sides of the trust game: more investing and much more paying back. On another cheap model (gemini-3.6-flash), which already cooperated almost fully, it did nothing measurable. **The social layer's effect depends on the model,** and the dependence is large.
- **It doesn't show:**
  - That RUE's talk and feelings, as opposed to the social-life paragraph, cause the Haiku effect (section 6.2).
  - That the effect generalises: to other works, other models, larger groups or longer games.
  - That the skimmer is held to account. He isn't (section 6.4).
- **The pilot's mechanism wasn't what was found.** The pilot suggested "talk keeps people investing". On Haiku, the bigger difference is in paying back, and it starts before any talk.

## 8. Reproduce

The Runs are saved in `prereg-runs/` (decision logs gzipped; 9 MB), with the analysis output in `prereg-runs/analysis.json`:

```
uv run scripts/prereg_analysis.py prereg-runs/gemini prereg-runs/haiku
```

To rerun from scratch, at tag `prereg-confirmatory-v1`:

```
uv run scripts/batch.py experiments/prereg-club.toml
uv run scripts/batch.py experiments/prereg-club-haiku.toml
```

Hosted models don't promise determinism, even with a fixed seed, so a rerun gives new samples of the same design rather than the same Runs.
