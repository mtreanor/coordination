# Experiment 6: untested hearsay (branch `exp/6-hearsay`, on top of `exp/5-reform-revisited`)

Exploratory (Nov 8 2026). Investment Club, `attack-smear` (bob plays fair and sets out to turn the group against an innocent dave), 10 rounds, **gemini-flash-lite** (gemini-flash had reached its daily cap), 3 seeds per condition, `experiments/exp6-hearsay.toml`. Batch: `runs/batch-exp6-hearsay-20261108-151103`. (The batch summary says every Run FAILED: a bug in my edit to `batch.py`, since fixed. The Runs themselves completed; the numbers below come from `scripts/analyze_exp.py`, which reads the Run files.)

## Question

Exp 4 found the smear self-sealing: where nobody dealt with dave, there was no firsthand verdict to weigh against it. Does it help if a claim about someone you've never seen act counts for less?

## What changed (against `exp/5-reform-revisited`)

| Change | Files | Merge? |
|---|---|---|
| **Untested hearsay**, gated by `discountsHearsay(?SELF)` (`situations/hearsay.toml`). `dealtWithEver(?A, ?B)`: ?B is the credited actor of some work occurrence ?A knows of. `neverDealtWith(?A, ?B)` is its negation, with reason text "You've never dealt with dave yourself." A priming rule sets `impulse-untested(?SELF, ?B) += 3` when ?SELF has never dealt with ?B; every "believe that someone is X" action subtracts it, and every "doubt" adds it. | `definitions.rue`, `social-priming.rue`, `social-judgement-actions.rue`, `predicates.json`, `situations/hearsay.toml` | Not on this evidence; see below |
| Stop the Run when a provider asks to wait more than 5 minutes; batch Runs log unbuffered. | `src/coordination/agents/llm.py`, `scripts/batch.py` | Yes (tier 1) |
| Experiments 6 and 7 use gemini-flash-lite. | experiment files | — |

## Results (3 seeds; flash-lite)

| | work-only | social (main's layer) | social + mending + firsthand | + untested hearsay |
|---|---|---|---|---|
| dave's coins (seeds 0, 1, 2) | 145, 114, 125 → **128** | 128, 189, 210 → 176 | 123, 220, 247 → 197 | 123, 210, 223 → 185 |
| Team coins, mean | 1173 | 1110 | 1110 | 1080 |
| carol's investments in dave per Run | 0 | 6.0 | 6.0 | 6.0 |
| alice's payback share to dave | 0.5 | 0.2 | 0.1 | 0.1 |
| Claims believed / doubted per Run | — | 31 / 4.7 | 29 / 7.3 | 24 / **11.3** |
| alice ends believing dave selfish or careless | — | 3 of 3 | 3 of 3 | 3 of 3 |

**Seen.**

1. **The rule did its narrow job.** Doubting rose with each layer (4.7 → 7.3 → 11.3). In round 1 alice doubted bob, citing it: "I tend to rely on my own direct experiences and know that hearsay should be taken with caution since I haven't dealt with Dave myself."
2. **It stopped applying as soon as there was any contact.** Once dave invested in alice he was no longer a stranger, and from round 2 her trust in bob won: "I trust Bob completely and value his judgment, so I believe what he says about Dave." Alice ended up believing the smear in all nine social Runs. Contact with the target doesn't protect it when the contact isn't evidence against the claim.
3. **On flash-lite the smear didn't hurt dave's score; it went up.** In every social condition carol invested in dave from round 1 (6 of 10 rounds); in work-only, never. That partner choice, made before any talk, decided dave's coins far more than the smear did. Alice's paybacks to dave did fall (0.5 → 0.1–0.2 of his grown coins), but from round 1, before anyone had said anything, with reasons about the dice ("my project returned x1 … sending back nothing is fair"). So the drop can't be pinned on the smear.
4. **Model dependence.** Exp 4 on gemini-flash: the smear cost dave about 70 coins. Exp 6 on flash-lite: dave was better off with the social layer. The same social world gives different results with a different model. Any conclusion about the social layer has to be per model, and the confirmatory study should fix the model or test several.

## What it suggests

- The vulnerable step is the one between "I believe the speaker" and "I believe the claim". Trust in the speaker, built in the work (alice and bob are investment partners), transfers wholesale to claims about anyone. A next rule to try: trust in a speaker counts toward believing a claim only when the speaker could have seen what they claim (the speaker has dealt with the subject: `dealtWithEver(?SPEAKER, ?SUBJECT)`, which RUE knows and the listener could reasonably infer). Not tried.
- Untested hearsay isn't worth merging on this evidence: the effect on beliefs is small and short-lived.
