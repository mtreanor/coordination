# Experiment 5: the reformed defector, revisited (branch `exp/5-reform-revisited`, on top of `exp/4-firsthand`)

Exploratory (Nov 8 2026). Not My Bug, `bob-reforms` (bob passes for three sprints, then reforms), plain work (fixes private), 10 sprints, gemini-flash, 3 seeds per condition. Five batches, each fixing what the one before showed: `experiments/exp5-*.toml`, `runs/batch-exp5{,b,c,d,e}-*`.

## Question

Exp 3: the social layer withheld reward from a reformed defector, and "bob is selfish" beliefs never revised. Does exp 4's firsthand first (belief revision from one's own verdicts), with mending, fix that?

## What happened, batch by batch

| Batch | Condition | bob's hours | Help to bob after sprint 4 (alice + carol + dave) | Passes to bob after sprint 4 | Self-serving blame* |
|---|---|---|---|---|---|
| 5 | work-only | **86.0** | **6.0** | 0 | — |
| 5 | social (main's layer) | 78.7 | 0.7 | 2.0 | 7 |
| 5 | social + mending | 78.3 | 1.0 | 2.0 | 2 |
| 5 | social + mending + firsthand (exp 4 as built) | 70.7 | 0 | **6.0** | 23 |
| 5b | … firsthand counts only what you saw someone do | 60.0 | 0 | **10.0** | 41 |
| 5c | … and no provenance lines in the Briefing | 59.3 | 0 | 10.0 | 42 |
| 5d | … and a grievance only for what you saw someone do | 61.0 | 0.7 | 10.0 | 42 |
| 5e | social (main's layer), **no lost-hours event** | 82.3 | 1.7 | **0** | — |
| 5e | social + mending + firsthand, **no lost-hours event** | **84.7** | **4.3** | **0** | — |

\* Work-judgement verdicts on "the team lost N hours to handoffs" that named the very colleague the judge had passed a bug to that sprint (per condition, 3 Runs).

## What changed (against `exp/4-firsthand`), and why

1. **Firsthand counts only what you saw someone do** (after batch 5). Dave kept passing to bob and then calling the team's lost hours "selfish of bob". That event is credited to nobody, so anyone can be held responsible, and the hours were lost *because dave passed to bob*. Exp 4's tier-2 rules counted that self-assigned blame as firsthand evidence ("You go by what you've seen for yourself" was listed as a reason for calling bob selfish). Tier-2 priming and belief revision now require `?SELF.role(?O, ACTOR, ?B)`: ?B is the occurrence's credited actor as far as ?SELF knows. `role` got a reason template ("You saw it: …"). → `social-priming.rue`, `social-drift.rue`, `predicates.json`. **Merge: yes.** It's what "firsthand" should mean.
2. **No provenance lines in the Briefing** (5c): tested whether repeating "alice told you they're selfish" every round kept hostility alive. No difference; `toldBy` is now recorded and shown on menus as a reason, but not in the state Briefing. → `predicates.json`. **Merge: either way.** Shorter Briefings favour hiding it.
3. **A grievance only for what you saw someone do** (5d): same reasoning, for mending's `freshGrievance`. No difference on its own. → `definitions.rue`. **Merge: yes, for consistency.**
4. **The real loop** (5b–5d were move-for-move identical): the *label action itself* lowers liking and trust and adds to a grudge (`call it selfish`: likes −1, trusts −1, grudge +1). So each sprint's self-serving verdict on the lost hours pushed dave's feelings about bob back to 0, and he passed again: "I have no trust or liking for Bob anyway." Nothing in drift or grievance rules can undo an effect applied every round.
5. **`not-my-bug-no-loss-event`** (5e): the work without the uncredited lost-hours event. The velocity is still in every Briefing; there's just no occurrence to pin on anyone. Retaliation ended at sprint 4 in all six Runs. → `src/coordination/work/not_my_bug.py` (`loss_event`), `work/__init__.py`.

## Seen

- **Uncredited group losses are a vehicle for blaming your victim.** In Not My Bug the person who passes a bug is the one who caused the handoff loss, and RUE's design lets them name anyone. Agents named the colleague they'd just passed to 7–42 times per condition. Once the social world turns that verdict into dislike, the passer has a standing reason to pass again. It's the most damaging dynamic found in these experiments, and it's in main's social layer too (main, seed 2: dave passed to bob from sprint 3 to the end).
- **With the loop removed, the improved social layer rewards reform**: 4.3 helps back to bob per Run against main's 1.7, and bob's hours (84.7) come close to work-only (86).
- The earlier exp 4 rules made things worse (bob 70.7), because they amplified the self-serving blame. That's a warning about tier-2 rules that read verdicts: they inherit every bias in how verdicts are made.

## For Mike to decide

- The uncredited lost-hours event was a deliberate design (ADR 0006: "hours lost to handoffs as an occurrence nobody is credited with", so attribution is the agent's choice). These Runs suggest that the choice, combined with label effects on feelings, creates a self-reinforcing scapegoat loop. Options: drop the event (5e); keep it but let a label that names someone you assigned blame to (rather than saw act) carry no feeling effects; or keep it as a feature, since it's real social behaviour, and measure it.
