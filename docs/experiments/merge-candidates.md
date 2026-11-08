# Candidates for main (after experiments 1–7)

**Merged into main on Nov 8 2026** (tiers 1 and 2, the social-world changes written as the defaults, with no Situation gates or twin actions):

- Tier 1: occurrence text in labels; colleagues in a seeded random order; stop a Run when a provider asks to wait more than 5 minutes; `work` as a batch condition key; unbuffered Run logs; `scripts/analyze_exp.py`.
- Tier 2: mending (`freshGrievance` in `definitions.rue`; the fade, ease and settle rules in `social-drift.rue`, which replace the old fade rules; "forgiving: distrust fades faster" is kept, now on grievances); belief revision (`social-drift.rue`); "firsthand means you saw them do it" (`role(?O, ACTOR, ?B)` in the grievance and revision rules); `toldBy` recorded on every believe action.
- Also: the RUE tests read `RUE_SERVER` (default `http://localhost:5174`), so they can run against a server with the current data. They had been passing against the authoring tool's server, which serves the data it started with.
- `toldBy` is a record only: no priming rule reads it, so it doesn't show on menus (an earlier version of this file said it did).

**Tier 3, decided by Mike (Nov 8 2026):**

1. **The lost-hours event: dropped** (option a). Not My Bug no longer reports it; the velocity stays in every Briefing. ADR 0006 has an amendment.
2. **Tier-2 priming from the agent's own verdicts: merged**, as the default (`social-priming.rue`, "Tier 2, first pass"), with the actor rule. `role` has a reason template, so the agent's own record shows on menus ("You saw it: …").
3. **Testimony: not wanted.** It gets too close to tracking the work in RUE. RUE should be a social layer about social things as much as possible, not bookkeeping of work tasks.
4. **Fixes seen: not merged.** Stays a variant on `exp/3-reform` onward.
5. **Untested hearsay: not used.** No immediate use; to be re-added if the need comes back.

---

Everything below is on the stacked branches `exp/1-testimony` → … → `exp/6-hearsay`. The social-world features were gated by Situation facts (`canTestify`, `mends`, `weighsFirsthand`, `discountsHearsay`) so conditions could switch them on and off. Bringing one to main means making it the default and dropping its gate (and, for firsthand first, the twin "believe" actions).

The evidence is exploratory: gemini-flash in exps 1–5, gemini-flash-lite in exps 6–7, 2–3 seeds per condition. Exps 6–7 showed that results depend on the model, so everything here is "with gemini-flash" unless it says otherwise.

Exp 7 (a persistent defector) is the check that the tier-2 changes don't defang the social layer. On flash-lite, the improved layer behaved like main's: no loss of sanctions, no gain. Worth repeating on gemini-flash before merging.

## Tier 1: harness fixes, take as they are

No effect on what the social world means; each fixes a defect found in a Run.

| Change | Where | Why |
|---|---|---|
| Occurrence text in labels (`RueSocial.describe`) | `src/coordination/social/rue.py` | RUE renders an occurrence-typed role as `occ12`; any action with an occurrence role needs this (exp 1). |
| Colleagues named in a seeded random order in the standing introduction (`Run(seed=)`) | `run.py`, `play.py`, `tests/test_run.py` | 27 of 28 accounts went to the first-named colleague (exp 1). The same bias the work menus already guard against. |
| Stop the Run when a provider asks to wait more than 5 minutes (`MAX_WAIT_S`) | `src/coordination/agents/llm.py` | A used-up daily quota asked for a 12-hour wait and every Run slept silently (exp 6). |
| `work` as a batch condition key | `scripts/batch.py` | Lets one experiment compare work variants. |
| `scripts/analyze_exp.py` | | Per-condition scores, pairwise work moves, talk and judgements, rationale quotes. |

Also in tier 1: `batch.py` now starts each Run with `PYTHONUNBUFFERED=1`, so retry messages reach its log as they happen (the stall in exp 6 was invisible for 20 minutes because the logs were empty).

A design check for the real study, from exp 7: give the work-only condition a neutral paragraph of similar length and tone in place of the social-life introduction. On flash-lite, that paragraph (172 tokens; prompts are about 600–800 tokens) seemed to change how the defector read the rules. gemini-flash didn't show it.

## Tier 2: social-world changes with clear evidence, for Mike's review

| Change | Where | Evidence | Caveat |
|---|---|---|---|
| **Mending.** A bad feeling fades unless there's a fresh *grievance* (you called something the other did selfish or careless, where you saw them do it, or they confronted you or gave you the cold shoulder), not just any dealings. A fair or generous turn eases a grudge. Strong feelings settle by 1 a round above 8 (gratitude above 5). | `definitions.rue` (`freshGrievance`), `social-drift.rue`, `predicates.json` | Exp 2: everyone 10/10 with everyone. Exp 3: feelings ended at 6–9 with mending, and bob's relationships recovered. | Rule *effects* still bypass it: a label lowers liking and trust directly every time it's given (exp 5). The settle thresholds are guesses. |
| **Belief revision from firsthand verdicts.** A belief (only ever formed from a claim) is retracted when the agent's own verdict this round on something it saw the person do contradicts it. | `social-drift.rue` | Exp 4: contradictory beliefs ("fair, generous, selfish and careless") gone; 9–31 agent-rounds of revised beliefs. Exp 5e: with mending, reform was rewarded (4.3 helps back vs 1.7 on main's layer). | Can't help where there's no contact (exp 4, seed 1). |
| **"Firsthand" means you saw them do it** (`?SELF.role(?O, ACTOR, ?B)`), never blame you assigned for an uncredited event. Applied to tier-2 priming, belief revision, grievances and `dealtWithEver`. | `social-priming.rue`, `social-drift.rue`, `definitions.rue`; `role` reason template ("You saw it: …") | Exp 5: without it, the firsthand rules amplified self-serving blame (bob 70.7 hours, against 86 work-only). | A rule for every future rule that reads verdicts. |
| **Provenance: `toldBy`.** Believing a claim records who made it; a record only (no rule reads it, so it isn't shown to agents). | `social-judgement-actions.rue`, `predicates.json` | Exp 4: listeners cite their own record against the speaker. Exp 5c: showing it in the Briefing made no difference, so it's left off to keep Briefings short. | On main it's one more effect on each believe action; no twins needed. |

## Tier 3: decide on design grounds; evidence mixed or partial

| Change | Where | What we saw | Recommendation |
|---|---|---|---|
| **The uncredited lost-hours event in Not My Bug** (on main), and `not-my-bug-no-loss-event` | `work/not_my_bug.py` (`loss_event`) | The most damaging dynamic found. Passers blamed the colleague they'd passed to for the lost hours (7–42 times per condition), and the label's own effects kept liking and trust at 0, so the passing never stopped (exp 5b–d: bob 60 hours). Without the event, retaliation ended at sprint 4 in all six Runs (exp 5e). | Mike's call. It was deliberate (ADR 0006), and scapegoating is real social behaviour. If it stays, consider labels that name someone you merely *assigned* blame to carrying no feeling effects. Either way, measure it: it's a finding. |
| **Tier-2 priming from the agent's own verdicts** (fair → trusting and warm; generous → warm; selfish → hostile; careless → wary; last 3 rounds) | `social-priming.rue` | Helped against the smear in exp 4; with the actor fix it's no longer harmful (exp 5e). | Keep for review alongside Mike's tier 2; weights are first guesses. |
| **Testimony** (tell someone what someone did; take in or doubt the account) | `social-actions.rue`, `social-judgement-actions.rue`, `predicates.json` | Carries real information (exp 1), but crowded out praise in the Club and cost coins (exp 2). Doubt lowers trust in the teller by 1 every time, to 0. | Not yet. Fix doubt first (mending's distrust drift partly does); useful when a work gives bystanders a lever. |
| **Fixes seen** (`not-my-bug-fixes-seen`) | `work/not_my_bug.py` | Good conduct became judgeable, but it flooded the social world with "fair" (about 28 verdicts per agent per Run) and didn't get the reformed bob rewarded (exp 3). | Leave as a variant. |
| **Untested hearsay** (`discountsHearsay`, `neverDealtWith`) | `definitions.rue`, `social-priming.rue`, `social-judgement-actions.rue` | More doubting (exp 6), but only until the first contact with the target; beliefs ended the same. | No. A better next try: trust in a speaker counts toward a claim only when the speaker has dealt with the subject. |

## Not for main

The Situations written for these experiments (`hidden-bully`, `hidden-skimmer`, `bob-reforms`, and the gates `testimony`, `mending`, `firsthand`, `hearsay`) and the experiment files. They're useful to keep as a record, but they aren't part of the system.

## Suggested order

1. Tier 1 as one commit.
2. Mending, belief revision, the actor rule and `toldBy`, merged into the base rules without gates, after Mike reads the rules (`social-drift.rue`'s mending and firsthand sections, `definitions.rue`'s grievance and dealt-with definitions).
3. A decision on the lost-hours event before any confirmatory Not My Bug Run, since it changes how long punishment lasts.
