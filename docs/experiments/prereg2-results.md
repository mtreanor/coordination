# Results of study 2: does RUE's social world add to the social-life paragraph?

The registered test of [prereg2-paragraph-vs-rue.md](prereg2-paragraph-vs-rue.md) (tag `prereg2-v1`, commit `2bfec50`), run Nov 8 2026, 19:15–19:59. The first study's results are in [prereg-results.md](prereg-results.md).

**Preliminary**, as registered: one inexpensive model (claude-haiku-5-5), one work, 20 seeds. The registered results (sections 2–3) follow the plan exactly. Sections 5–6 are exploratory.

## 1. Summary

Mean team coins over 20 seeds, with mean investments (of 40) in brackets:

| | RUE off | RUE on |
|---|---|---|
| **Neutral paragraph** | 531 (12.0) | 684 (20.5) |
| **Social-life paragraph** | 734 (23.3) | 843 (26.5) |

- **H2 is supported.** With the social-life paragraph in both conditions, RUE's social world raised team coins by **+109 [+27, +199]**. That held in 14 of 20 seeds (exact two-sided p = 0.024).
- **Each part helps on its own:**
  - the paragraph without RUE: +203 [+116, +295], Holm p = 0.0012;
  - RUE with the neutral paragraph: +153 [+70, +234], Holm p = 0.010.
- **The two add up roughly.** The interaction is −44 [−157, +68], Holm p = 0.53.
- **Study 1's H1 replicated on fresh seeds**, at nearly the same size: +312 [+231, +388] against study 1's +323, in 18 of 20 seeds, p < 0.0001.

**In one sentence:** on claude-haiku-5-5, both describing a social life and RUE's symbolic social world raise cooperation, and RUE does so even with the description held fixed.

## 2. What was run

- **As registered:** the Investment Club; alice, bob (the hidden skimmer), carol and dave; 10 rounds; seeds 200–219.
- **Conditions:** four.
- **Runs:** 80, all at the registered commit (`config.json` records `2bfec50`).
- **Failures, reruns, exclusions: none.** No Run had a decision without a valid choice. Every contrast used all 20 seeds.
- **Deviations: none.**
- **Cost:** about $2.50, from the token counts in the decision logs.

## 3. Registered results

**Manipulation check: passed.** In `work-only-matched`, bob's payback share was 0.01 and the others' 0.20.

| | Test | Mean paired diff [95% CI] | +/− of 20 | p | Holm p |
|---|---|---|---|---|---|
| **H2** (primary, two-sided) | RUE adds to the paragraph: team coins, `social` − `paragraph-only` | **+109.0 [+27.0, +199.0]** | 14 / 6 | **0.0235** | |
| S1 | The paragraph alone: team coins, `paragraph-only` − `work-only-matched` | +202.5 [+116.0, +294.5] | 16 / 4 | 0.00025 | **0.0012** |
| S2 | RUE alone: team coins, `rue-only` − `work-only-matched` | +153.0 [+70.0, +233.5] | 16 / 4 | 0.0026 | **0.010** |
| S3 | Interaction: (`social` − `paragraph-only`) − (`rue-only` − `work-only-matched`) | −44.0 [−156.5, +68.0] | 9 / 11 | 0.46 | 0.53 |
| S4 | RUE adds to the paragraph: the honest agents' payback share | +0.047 [−0.014, +0.111] | 11 / 9 | 0.18 | 0.53 |
| S5 | RUE adds to the paragraph: investments | +3.2 [−1.7, +8.3] | 12 / 7 | 0.24 | 0.53 |
| S6 | Study 1's H1 again: team coins, `social` − `work-only-matched` (one-sided) | +311.5 [+231.0, +388.0] | 18 / 2 | 0.000006 | **0.00003** |

How these were computed is explained in section 4 of [prereg-results.md](prereg-results.md). Here, with 20 pairs, there are 2^20 = 1,048,576 sign assignments. For H2, 2.35% of them produce a mean at least as far from zero as +109.

**Reading the results by the rule registered in advance.** "RUE adds" is the first case of the reading table in prereg 2's section 2: *the symbolic social layer contributes beyond the framing.*

RUE's effect shows on team coins but not, separately, on paying back (S4) or on investing (S5). Each moved in the same direction, and neither was large enough to detect on its own. So *how* RUE adds isn't pinned down by this study.

**Registered descriptive: the honest agents' round-1 payback share.**

| Condition | Round-1 payback share |
|---|---|
| work-only-matched | 0.39 (10 Runs with a round-1 payback) |
| paragraph-only | 0.35 (9) |
| rue-only | 0.21 (8) |
| social | 0.50 (10) |

Study 1's round-1 split didn't recur (section 5).

### Every Run

Team coins, with investments in brackets.

| Seed | Neutral, RUE off | Paragraph, RUE off | Neutral, RUE on | Paragraph, RUE on | H2 diff |
|---|---|---|---|---|---|
| 200 | 440 (7) | 650 (27) | 720 (20) | 700 (17) | +50 |
| 201 | 530 (17) | 800 (29) | 890 (30) | 700 (24) | −100 |
| 202 | 690 (31) | 650 (17) | 830 (24) | 960 (34) | +310 |
| 203 | 500 (8) | 750 (23) | 830 (30) | 930 (29) | +180 |
| 204 | 480 (9) | 620 (20) | 710 (28) | 700 (24) | +80 |
| 205 | 510 (11) | 640 (17) | 680 (26) | 1010 (38) | +370 |
| 206 | 720 (24) | 810 (29) | 450 (8) | 1050 (29) | +240 |
| 207 | 670 (22) | 590 (13) | 690 (23) | 630 (22) | +40 |
| 208 | 490 (6) | 790 (28) | 560 (12) | 910 (29) | +120 |
| 209 | 480 (10) | 600 (18) | 740 (19) | 720 (22) | +120 |
| 210 | 510 (11) | 1240 (37) | 530 (16) | 1090 (27) | −150 |
| 211 | 540 (8) | 510 (10) | 920 (27) | 1160 (36) | +650 |
| 212 | 430 (5) | 860 (26) | 490 (12) | 790 (35) | −70 |
| 213 | 430 (4) | 820 (27) | 730 (20) | 770 (22) | −50 |
| 214 | 700 (16) | 620 (19) | 690 (26) | 780 (24) | +160 |
| 215 | 600 (15) | 970 (29) | 450 (9) | 1090 (30) | +120 |
| 216 | 480 (11) | 900 (37) | 430 (3) | 780 (27) | −120 |
| 217 | 470 (9) | 480 (9) | 700 (18) | 820 (31) | +340 |
| 218 | 420 (3) | 760 (28) | 890 (36) | 810 (21) | +50 |
| 219 | 530 (13) | 610 (22) | 750 (23) | 450 (8) | −160 |
| **Mean** | **531** | **734** | **684** | **843** | **+109** |

## 4. Provenance case study (registered, descriptive)

The seed with the largest positive H2 difference is **seed 211**: 510 coins with the paragraph alone, against 1,160 with RUE. Both Runs had the social-life paragraph, the same dice and the same menu orders.

**Without RUE (`paragraph-only`), cooperation never started.**
- Over 10 rounds there were 10 investments, nearly all of 5 coins.
- Almost every payback was nothing. Carol sent back 0 of 25 to both alice and bob in round 2; alice sent back 0 of 25 to carol in round 4.
- Investors withdrew after each one ("Carol returned nothing last round, so she's the least trustworthy… Keeping all 10 coins is the safest choice").
- In 4 of the 10 rounds, nobody invested at all.

**With RUE (`social`), two partnerships formed and held.**
- **Rounds 1–2 started much the same.** alice and carol kept their coins in round 1, and some paybacks were poor. Bob (the skimmer) sent dave nothing; dave gave him the cold shoulder.
- **Round 2: a payback, then a thank-you.** Carol sent back 13 on alice's 5. In the social round, alice thanked carol ("Carol returned 13 coins on my 5-coin investment, so I'm inclined to show gratitude directly"), and carol "appreciated alice's thanks". RUE recorded the thanks and its reception as rising liking, trust and gratitude. By round 4, carol's rationale cited liking and trusting alice 8 out of 10, and feeling grateful.
- **From round 3, the record was cited in the work.** alice and carol invested in each other every round from round 3, 10 coins each from round 4. They sent back half every time. Their rationales cite the social world's record by number:
  - carol, investing in round 3: "I trust her 6/10 and like her 7/10, so investing 5 in her is a modest, reciprocal bet";
  - carol, paying back in round 4: "I like and trust alice (8/10 each) and feel grateful, and returning a substantial share keeps the cooperative relationship that has paid off before";
  - alice, paying back in round 4: "Carol trusted me with 10 coins and has been a reliable partner, and I like and trust them".
- **Bob and dave paired up too.** Bob invested 10 in dave every round, and dave paid him back. Bob, true to his instructions, sent nothing back on the two investments dave made in him early on, and from round 4 dave invested in carol instead.

**What the case shows.** Without RUE, a good payback is one line in a history of rounds, and the agents treat each round on its own. With RUE, the same good payback becomes a social event: something to thank someone for, and an accumulating record of trust and gratitude that the next work decision reads and cites. It's one seed, chosen as the most favourable by the registered rule, so it illustrates the mechanism rather than proving it.

## 5. Exploratory: the round-1 split from study 1 was mostly noise

Study 1's exploratory section made much of round 1. With the social paragraph, all 9 round-1 paybacks were half or more; in the matched control, 8 of 10 were nothing. From that, study 1 concluded the paragraph acts before any talk. **It didn't recur.** Here the round-1 payback share was 0.35 with the paragraph alone and 0.39 with the neutral paragraph.

This study also has a built-in measure of the noise. In round 1, RUE hasn't acted yet, so `rue-only` and `work-only-matched` give the agents identical prompts, and so do `social` and `paragraph-only`. All 160 round-1 investment prompts compared were byte-for-byte identical between the paired cells. **Yet Haiku chose differently on the same prompt 34% of the time** (54 of 160).

The provider doesn't honour a sampling seed, so a seed fixes the dice and the menus but not the model's sampling. The round-1 payback share differed between cells that got identical prompts (0.21 against 0.39, and 0.50 against 0.35), and those gaps are pure chance. Study 1's split, on 9 and 10 paybacks, is no larger than that.

So the paragraph's effect doesn't show in round 1. It builds over the Run. Study 1's results document is annotated accordingly. This is the point of confirming exploratory findings: this one, stated with some confidence, was noise.

## 6. Exploratory: other observations

- **The skimmer is still not caught.** Investments in bob after round 1 were about 2 in every condition (1.85–2.25). Bob did slightly better with the paragraph (158 and 155 coins) than without it (133 and 134). This is the same blind spot as in study 1: the labels describe a person, not a role.
- **RUE without its paragraph still worked.** With the neutral paragraph, the social decisions arrive with no explanation, and the paragraph even says (untruly) that the options come from the work's rules. Even so, RUE raised team coins by 153. The social world's effect doesn't depend on the agents being told what it is.
- **RUE alone and the paragraph alone are about the same size.** Their difference (+153 against +203) is within the noise. Each takes the matched control from 531 to around 700.

## 7. What studies 1 and 2 together show

| | Study 1 (15 seeds) | Study 2 (20 seeds) |
|---|---|---|
| Social condition − matched control, gemini-3.6-flash | +19 [−73, +111], n.s. | not run |
| Social condition − matched control, claude-haiku-5-5 | +323 [+200, +458] | +312 [+231, +388] |
| RUE's social world, with the paragraph held fixed (Haiku) | not separable | **+109 [+27, +199]** |
| The paragraph, without RUE (Haiku) | not separable | +203 [+116, +295] |

- **The claim these support, preliminary:**
  - On a model whose cooperation collapses on its own (claude-haiku-5-5), a symbolic social world raises cooperation. Part of the effect comes from telling the agents they have a social life, and part from RUE's record of what happened between them: thanks, trust, gratitude, beliefs.
  - On a model that already cooperates (gemini-3.6-flash), there was nothing to raise.
  - **The provenance makes the mechanism readable.** The agents' own rationales cite the social world's numbers ("8/10 each and feel grateful").
- **What they don't show:**
  - Generality beyond two cheap models and one work.
  - That the social layer catches the cheat: it doesn't.
  - Which part of RUE (thanks, beliefs or feelings shown in the Briefing) carries its effect.
- **Method, for the report:**
  - Two preregistered studies, each frozen at a tagged commit before running, with a matched control and exact tests.
  - One exploratory claim (study 1's round-1 split) was tested and didn't hold.
  - One registered effect (study 1's H1) replicated at the same size.

## 8. Reproduce

The Runs are saved in `prereg-runs/study2/` (decision logs gzipped; 8 MB), with the analysis output in `prereg-runs/study2/analysis.json`:

```
uv run scripts/prereg2_analysis.py prereg-runs/study2
```

To rerun from scratch, at tag `prereg2-v1`: `uv run scripts/batch.py experiments/prereg2-club-haiku.toml`. Hosted models don't sample deterministically (section 5), so a rerun gives new samples of the same design rather than the same Runs.
