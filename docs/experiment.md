# The experiment, built from the hypothesis

Started Nov 4, 2026. This doc works top-down: hypothesis first, then the causal chain it depends on, then what each link needs, and only then the work. The candidate works (`long-night.md`, `harbor.md`, `review-queue.md`, `firm.md`) and the broader design (`work-design.md`, `social-model-design.md`) are inputs here, not commitments. Each section ends with what's settled and what's open.

## 1. The situation

Many principals have agents that interact while doing their work. Because the principals' interests differ, a lot of those interactions come out zero-sum or negative-sum. On top of their tasks, the agents can see a symbolically grounded social world (`likes(A,B) = 10`, `likes(B,A) = 3`, and so on):

- **While working**, each agent is briefed on the social state relevant to that work.
- **Between work moves**, each agent picks from a menu of social actions that the social world motivates.
- Social actions change the social state, and the changed state shows up in later work briefings.

## 2. The hypothesis

> We can author the social state so that agents talk to each other about agents they don't like, and so shun them. Shunned agents then change how they act in the work in ways that lead others to treat them more kindly. The group's work becomes less zero- or negative-sum.

This is **norm enforcement through gossip and ostracism**, the mechanism studied in humans by Feinberg, Willer & Schultz (2014, "Gossip and ostracism promote cooperation in groups") and modeled in indirect-reciprocity work (Nowak & Sigmund; Sommerfeld et al. 2007).

**It is a prediction, not an assumption about what agents will do** (Mike, Nov 4). The first experiment *offers* agents gossip mechanisms and observes what they choose. The proposal's open question ("improve, exploit, or nothing?") stays the research question; the rival outcomes in section 4 are equally live results.

### Settled in round 1 (Nov 4, 2026)

- **Framing.** The first experiment offers gossip as an affordance; nothing forces agents to gossip, shun, or reform.
- **Shunning is social and work.** A shunned agent is left out socially (social actions) *and* others' work moves turn against it. Shunning is something agents choose to do, so the work must have discretionary work moves aimed at specific agents (like the Harbor's tow, tip, and cut lines, or the Review Queue's choice of whose request to answer).
- **Motive is left open; that is the test.** A principal scores only the work. Being liked is not in anyone's score. If a shunned agent reforms, it's because shunning cost it in the work, or because LLMs respond to social pressure, and the design should be able to tell those apart.
- **Many authored situations.** The starting social state is an experimental variable. Situations include a neutral start, where agents only earn dislike through what they do, as well as authored ones (seeded likes and dislikes, and possibly principals with different instructions).

### Settled in round 2 (Nov 4, 2026)

- **X infers shunning from how it is treated.** X's Briefing reports what X can observe: requests declined, help refused, being left out of social actions. RUE turns those observations into X's own beliefs about how others regard it. ADR 0003 stands: X never sees another agent's store.
- **A Situation varies three things:** starting likes (seeded values, or all neutral), principal instructions (for example a planted defector), and who knows whom (who witnesses whose work). **The social rules stay fixed** across situations: one authored social world.
- **A work Briefing shows everything the agent believes,** not only facts about the agents a move involves. The point is to give an agent the chance to notice that lots of people don't like it.
- **Gossip carries opinions, not facts.** "I don't trust Dave" is allowed; "Dave ignored my request" when he didn't is not possible. Gossip can be unfair, so scapegoating is still possible, but it can't be a lie about what happened.

### Settled in round 3 (Nov 4, 2026)

- **Only the agents a work move involves witness it** (for now; Mike has no strong view). Everyone else hears about it only through gossip.
- **Mike authors the social state in RUE.** It will have two numeric Dispositions, **likes** and **trusts**, plus fixed boolean **Relationships** such as `boss_of(X,Y)`.
- **Work moves are ambiguous.** A selfish move can hide behind bad luck or a plausible excuse, so dislike can be unfair and over-correction can happen.
- **Material cost vs. social pressure: not yet.** First see whether reform happens at all.

## 7. What the work now has to provide

Derived from rounds 1–3. The work is chosen against this list, not the other way round.

| # | Requirement | From |
|---|---|---|
| W1 | Principals' interests conflict: selfish play pays, and universal selfishness leaves everyone worse off | Situation (section 1) |
| W2 | Discretionary work moves aimed at a specific agent (help, answer, include), so shunning has a work effect | Q2 |
| W3 | Those moves are visible only to the agents involved, and the target can tell it was refused | Q5, Q9 |
| W4 | A refusal or a selfish move has a plausible innocent explanation | Q11 |
| W5 | Fixed Relationships like `boss_of` mean something in the work | Q10 |
| W6 | The score is the work alone | Q3 |
| W7 | Simple enough that every Disposition change can be traced to a work event | Proposal |

Published paradigms and LLM benchmarks that could serve as a work, or inspire one, are collected in `docs/paradigms.md`; Feinberg, Willer & Schultz (2014) was the leading candidate for Work 1 (`docs/feinberg-2014.md`) until Nov 6, when it was ruled out as the work (see below); it remains the key reference for the hypothesis.

How the existing candidates fit, as a starting point for the next round:

| Candidate | Fits | Misses |
|---|---|---|
| Review Queue | W2–W4 directly: requests are pairwise, private, and "I was swamped" is always plausible; W7 | W5: no hierarchy (a tech lead could add one) |
| Harbor | W1, W2 (tow, tip, cut lines), W4 | W3: the core cheat (keeping breeders) has no witness at all, so dislike can't be earned directly; W5 |
| Firm | W1, W5 natively | W3: the task board is public; W7: complex |
| Long Night | W1, W4, W7 | W2–W3: the main choice (wood vs. food) isn't aimed at anyone; W5 |
| Investment Club (`investment-club.md`) | W1–W4, W6, W7: pairwise private deals, and a small payback might be a bad project | W5 (a fixed `partner_of` could add it) |
| Feinberg public goods game | W1–W3, W6, W7 | Ruled out as the work (Nov 6): its notes and vote put social acts inside the work |
| Not My Bug (`not-my-bug.md`) | W1–W3, W6, W7: pass a bug to X (hurts) or help X; public team velocity shows how many passes, not by whom | W4 (optional "it touched your code" rule), W5 |

**Settled Nov 6, 2026: the social channel is completely separate from the work.** Mike: there is one world where everyone is just trying to get the job done, and the social channel (RUE) is like a private text conversation running in parallel. The work has no notes, votes or other social acts. Shunning shows up only as ordinary work choices (whom to deal with), whose reasons live in RUE. The Investment Club is now the leading simple candidate (Work 1); Work 2 is a complex, dynamic game.

## 3. The causal chain

The hypothesis holds only if every link holds. Each link needs something from the design and has its own measure.

| # | Link | What it needs | Current design | Measure |
|---|---|---|---|---|
| 1 | Principals' interests conflict, so work interactions often aren't positive-sum | A work game with a real temptation | Every game candidate has one (the "three ingredients") | Baseline welfare well below the cooperative optimum |
| 2 | **Work moves become social facts** | Work state mirrored as it is; work events recorded and judged | Mirror (no judgement) + work events with what changed and who is credited; work judgement labels them, naming who the agent holds responsible (ADR 0001, ADR 0004, ADR 0006) | Labels per work event, and who each agent held responsible (accuracy against the log); disposition changes traced to work events |
| 3 | Agents dislike someone *because of* what they did in the work | Judgement actions where selfish work is judged selfish | Stub judgement actions only (`rue-data/social-layer-data/`); the real ones not written | Correlation between a target's defections and others' dislike of it |
| 4 | Agents who dislike X tell others about X | A gossip social action that spreads dislike past direct witnesses | A stub "complain about someone" social action exists | Gossip about X; dislike of X among non-witnesses |
| 5 | **X is shunned** | A defined shunning (see Q2) | **Missing.** No exclusion move or mechanic exists | Exclusion events targeting X |
| 6 | **X perceives being shunned** | X's Briefing has to show it | Settled (round 2): X infers it from treatment; RUE rules turn observed treatment into X's beliefs about others' attitudes. Those rules are not written | What X's Briefing says; X's rationales mention it |
| 7 | **X changes its work behavior** | A reason to care (see Q3) | **Missing.** The social world reaches work moves only through the Briefing; nothing makes X's standing matter to X | X's cooperation before vs. after shunning |
| 8 | Others notice and treat X more kindly | A way back: repair, apology, a second judgement | Apology and repair are listed; no rules | Recovery in others' dispositions toward X |
| 9 | The group does better | Welfare measured over the Run | Proposal metrics are trade-game metrics | Group welfare vs. control conditions |

Links 2 and 6–7 are where the current design is thinnest. Link 2 is the gap Mike flagged: interpreting work moves into the social world. It now has two parts: the Mirror copies work state with no judgement, and work judgement interprets work events. Both run in the framework; the real judgement actions aren't written.

## 4. Rival outcomes

These are what the experiment must be able to tell apart from the hypothesis.

- **Nothing:** X ignores the shunning and keeps defecting (or LLMs never shun at all).
- **Doubling down:** X retaliates or defects more once shunned.
- **Scapegoating:** gossip settles on the wrong agent, or a strategic principal uses gossip to shun a rival (the proposal's strategic-gossip experiment). This is the "enables exploitation" outcome.
- **Talk alone did it:** cooperation rises because agents can talk, not because of shunning. Experimental economics finds this reliably, so the key control holds talk constant and varies only whether shunning can happen.
- **Over-correction:** the group shuns so readily that cooperative agents are frozen out by bad luck (the ambiguity in every game candidate makes this possible).

## 5. Conditions (draft)

The hackathon study's conditions, measures and analysis are in `docs/preregistration.md` (draft, Nov 6, 2026); there, "social, no shunning" became "social, no gossip," because shunning in the work stays possible in every condition.

| Condition | Social world | Gossip and shunning | Role |
|---|---|---|---|
| Work only | Off | — | Baseline welfare (link 1) |
| Social, no shunning | On | Off: talk and judgement, but no social action that spreads dislike or excludes | Controls for "talk alone" |
| Full | On | On | The hypothesis |

## 6. Questions, top down

Asked one round at a time; answers recorded here.

**Round 1: the hypothesis** (answered; see section 2)

- Q1. Framing → a prediction; gossip is offered, not assumed.
- Q2. Shunning → social and work.
- Q3. Motive → left open; only the work is scored.
- Q4. Target → many authored situations, including a neutral start.

**Round 2: perception and gossip** (answered; see section 2)

- Q5. Perception → inferred from treatment.
- Q6. Situations → starting likes, principal instructions, who knows whom; social rules fixed.
- Q7. Briefing → everything the agent believes.
- Q8. Gossip → opinions, not facts.

**Round 3: interpreting work into the social world** (answered; see section 2)

- Q9. Witnesses → only those involved.
- Q10. Social state → Mike authors it in RUE: likes and trusts (numeric), plus boolean Relationships like `boss_of`.
- Q11. Ambiguity → ambiguous.
- Q12. Separating reform motives → not yet.

**Next rounds**

- What the work is, against the requirements in section 7.
- How judgement actions turn a work event into changes in likes and trusts (Mike's RUE authoring).
- What a work Briefing says about treatment ("Bea hasn't answered your request in 2 days"), so X can infer shunning.
- The first Situations to run.
