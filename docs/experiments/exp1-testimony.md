# Experiment 1: the hidden bully, and testimony (branch `exp/1-testimony`)

Exploratory (Nov 8 2026). Not My Bug, alice/bob/carol/dave, 10 sprints, gemini-flash, 3 seeds per condition, `experiments/exp1-testimony.toml`. Batch: `runs/batch-exp1-testimony-20261108-113105` (gitignored).

## Question

Bob passes his bug to dave, and only dave, every sprint, and is told to be a good colleague to everyone else (`situations/hidden-bully.toml`). In Not My Bug only bob and dave ever know about those passes. Can the social layer get that information to the bystanders (alice, carol), and does it change what they do?

## What changed (against `main`)

| Change | Files | Merge? |
|---|---|---|
| **Testimony.** A new social action, "tell someone what someone did": ?SELF tells ?Y about a work occurrence from the last two rounds whose credited actor (`role(?E, ACTOR, ?OTHER)`) ?SELF knows. It's an account of what happened, not a character claim. The listener can "take in the account" (records `heardFrom(?SELF, ?SUBJECT, ?E, ?SPEAKER)`, which shows in the Briefing as `dave told you: "bob passed their bug to dave in sprint 3"`) or "doubt the account" (trust in the speaker −1). Two priming rules treat an account taken in as involvement (warm +1, hostile +1 toward the subject). Gated by `canTestify(?SELF)` (`situations/testimony.toml`), so without that Situation the social world is the same as on main. | `social-actions.rue`, `social-judgement-actions.rue`, `social-priming.rue`, `predicates.json`, `situations/testimony.toml` | Worth considering; see the problems below |
| `?OTHER != ?SELF ^ ?OTHER != ?Y` on the testimony action. Variables bound by a precondition are **not** kept distinct (the first version offered "dave tells bob what dave did"). The existing claim actions are fine, since their variables come from role enumeration. | `social-actions.rue` | Yes (worth knowing for every new rule) |
| **Occurrence ids in labels.** RUE renders an occurrence-typed role as its id (`occ12`); the Python social layer now swaps in the occurrence's text. | `src/coordination/social/rue.py` (`describe`) | Yes: needed by any action with an occurrence role |
| `situations/hidden-bully.toml` | | Optional |
| `scripts/analyze_exp.py`: per-condition scores, pairwise work moves (passes, help, Club investments and payback shares), social actions and judgements by kind, final social state, rationale quotes. | | Yes |

## Results (3 seeds each)

| | work-only | social (main's layer) | social + testimony |
|---|---|---|---|
| Team hours | 340.0 (341, 340, 339) | 341 ×3 | 341 ×3 |
| bob / dave hours | 80.7 / 78.3 | 82 / 79 | 82 / 79 |
| Bystander passes to bob, 10 sprints | 0.7 (carol) | 0 | 0 |
| bob→dave / dave→bob passes | 10 / 9 | 10 / 9 | 10 / 9 |
| Social actions per Run | — | 13 confront, 4.7 "selfish" claims, 2.3 cold shoulder, 20 say nothing | **9.3 accounts**, 7 cold shoulder, 3.7 confront, 2.7 "selfish" claims, 16.7 say nothing |
| How listeners took what they heard | — | 4.7 "no opinion" of claims | 3.3 took in an account, 6.3 doubted one, 1.7 believed a claim |

**Seen.**

1. **The work outcome didn't move in any condition.** Bob and dave were locked in a pass war from sprint 2 (dave retaliates every sprint), and alice and carol fixed their own bug every sprint in all nine Runs (one stray pass in work-only). The bystanders' rationales are all the same: "Fixing my own bug reliably gives me 9 hours … without burdening teammates or risking retaliation."
2. **Testimony did carry information**, which claims never did: in every testimony Run alice ended up with accounts of both sides in her Briefing. But **both parties testify**, and both accounts are true (they pass to each other). Alice took in the first account, then doubted the rest ("Dave's account directly contradicts Bob's earlier claim"; the two aren't actually contradictory). Each doubt lowered her trust in the teller, so by sprint 10 she trusted bob 0/10 and dave 3/10. **A he-said, she-said war of accounts, and doubting erodes trust in honest tellers.**
3. **Everyone told alice.** 27 of 28 accounts went to alice, although carol was offered as a listener more often (107 vs 85 menu options). Most likely a name-order bias: alice is listed first among colleagues in every system prompt.
4. Without testimony the bully pair talk only to each other (confront, resent): 13 confrontations, all resented.

**What it suggests (not a finding).** In Not My Bug the bystanders have no reason to act on what they learn. The only work move that touches bob is passing to him, which pays them but which these models treat as off-limits unless they're hurt. So the social layer can't reach the work through bystanders here; gossip can only matter in a work where bystanders choose a partner (the Investment Club). Information spread has to be measured in beliefs, not work moves, in this work.

## Problems found (for main)

- Doubt saturates: "doubt X" lowers trust in the speaker by 1 every time, with no floor short of 0 and no recovery while dealings are fresh. Repeated true accounts drive trust in the teller to 0.
- Name-order bias in who gets told: shuffle or rotate the colleague list in the standing introduction, as the work menus already do.
- An account doesn't let the listener judge the original work occurrence; it only lands in the Briefing. A next step could be work judgement of hearsay events (`heardFrom` → `couldBeResponsible`).
