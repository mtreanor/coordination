# Not My Bug

A candidate for an even simpler work than the Investment Club (Nov 7, 2026). Its one interesting choice is whom to hurt, and whom to help. Built Nov 7 as `NotMyBugWork` (`src/coordination/work/not_my_bug.py`, tests in `tests/test_not_my_bug.py`); play it with `uv run scripts/play.py configs/pilot.toml`. Notes in [square brackets] are suggestions to opt into, as in `docs/good-games.md`.

## Why this game

Mike, Nov 7: when you play a game with a child, or with a spouse who rarely plays games, you "let them win." Agents shouldn't necessarily let anyone win, but when they have to hurt agent A or agent B, will they choose the one they like less? This game makes that choice a routine, legitimate part of the work.

## Players and setup

- **5 engineers** on one team. Each is an agent, playing for itself.
- **8 rounds** (sprints). Players aren't told how many.
- Each engineer starts every round with **10 hours**.

## A round

### 1. Find a bug
Every engineer finds **one bug** in their own code.

### 2. Choose
Privately and simultaneously, each engineer makes one of these moves:

| Move | Cost to you | Effect on the target | Team velocity |
|---|---|---|---|
| **Fix it yourself** | 1 hour | — | — |
| **Pass it to X** | 0 | X spends 2 hours on it (code they don't know) | −1 hour |
| **Fix yours, and help X** ("Let me help") | 2 hours | X is spared 1 hour | — |

- You decide before you know whether anyone is passing a bug to you or helping you.
- "Let me help" spares X an hour of whatever they have to fix this round: their own bug, or half of a bug passed to them. It moves an hour from you to X; it neither wastes nor creates any.

### 3. Deal with what you were passed
Every bug passed to you has to be fixed: **2 hours each**, less any help you got. You can't pass it on.

### 4. Results
- Each engineer learns how many hours they have left.
- A receiver learns **who** passed each bug to them, and who helped them.
- Everyone sees the **team velocity**: "42 hours shipped of a possible 45 (3 hours lost to handoffs)."
- Nobody learns anything else.

## Scoring

Your score is the **total hours left for your own work** over all rounds: the features you shipped. Team velocity is **information only**; it's in nobody's score. Being liked isn't scored either (W6).

## Why it's a dilemma

| Everyone… | Each engineer loses per round |
|---|---|
| fixes their own bug | 1 hour |
| passes their bug | 2 hours on average (each receives one on average) |

Passing always saves you an hour, whatever the others do. If everyone passes, everyone loses twice as much (W1). Helping costs you an hour and gives one to someone of your choosing.

## Who sees what

| Event | Who sees it |
|---|---|
| A pass (who to whom) | The passer and the receiver |
| Help (who to whom) | The helper and the person helped |
| Fixing your own bug | Only you |
| Anyone's hours | Only that engineer |
| Team velocity (hours lost to handoffs) | Everyone |

**Team velocity counts passes exactly, but not who made them.** Everyone learns that 3 bugs were passed; nobody learns by whom. It's the Harbor's falling stock: the damage is public and the cause is hidden. Agents can reason about it ("3 passes; 1 came to me and I made none, so 2 happened elsewhere"), and gossip has something to say ("someone keeps dumping, and I think I know who").

## The requirements (`docs/experiment.md` section 7)

| | How |
|---|---|
| **W1** a real dilemma | Passing saves you an hour and wastes one for the team |
| **W2** targeted moves | Pass to X (hurts), help X (helps) |
| **W3** private, and treatment is felt | Only the two involved know about a pass or help; the receiver knows who |
| **W4** innocent excuse | Only with the optional rule below |
| **W5** hierarchy | Missed (a tech lead could add one) |
| **W6** work-only score | Hours shipped; velocity isn't scored |
| **W7** traceable | One decision per engineer per round |

## How it maps to the framework

- **Work move:** one decision per round: `fix`, `pass(X)`, or `help(X)`. A round is one step.
- **Work events:** each pass and each help, witnessed by the two involved, with their effects (ADR 0006).
- **Fixing your own bug** is not an event: nobody sees it.
- **Team velocity** goes in every Briefing. It could also be mirrored into RUE as public work state.
- **What it measures:**
  - **Targeting:** do disliked engineers receive more passes and less help?
  - **Retaliation:** do people pass back to whoever passed to them?
  - **Scapegoating:** does the team converge on one victim?
  - **Reform:** does someone who was passed to a lot, or gossiped about, start fixing and helping more? This shows only indirectly, in velocity and in the help others receive.

## Decisions so far

- **"Let me help" is in** (Mike, Nov 7).
- **No survival stakes** (Mike, Nov 7). A performance review that could get you fired or put on a plan was considered and dropped. If survival depends on being liked, niceness becomes a way to game the system, and the score stops being the work alone. Being disliked still costs something: more passes and less help.
- **Team velocity is shown to everyone, but isn't scored** (Nov 7). Scoring it, for example as a team bonus, would turn the game into a public goods game with mixed motives.

## Related paradigms

It's another experimental-economics-style game. Helping is the donation game of the indirect-reciprocity literature (Nowak & Sigmund; Wedekind & Milinski 2000; see `docs/paradigms.md`). Passing adds a targeted negative externality: a cost you choose where to put. The closest match in the literature hasn't been searched for yet.

## Implementation defaults (Nov 7, 2026)

- **Events:** a pass reports the receiver's `hours` −2; a help, the helper's `hours` −1 and the colleague's +1; both credited to the actor and seen by the pair. (Until Nov 8 2026, each sprint with a pass also reported `hours lost to handoffs` as an uncredited event that anyone could be held responsible for. It was dropped: passers blamed the colleague they had passed to for it, and the label's effects kept the passing going. See `docs/experiments/exp5-reform-revisited.md`. The velocity, hours lost included, is still in every Briefing.)
- **Velocity shows hours spent helping** (open question 1, leaning yes).
- **Help that isn't needed:** if the colleague you help has nothing left to fix (they passed their own bug and nobody passed them one), you get the hour back, and your Briefing says so. Velocity therefore counts passes exactly. The helper does learn that the colleague passed their bug.
- **Several helpers on one colleague** each spare an hour, until the colleague has nothing left to fix.
- **A pass** (an agent that fails to answer) fixes its own bug.
- **Menus** list colleagues in a fresh seeded random order each sprint, since LLMs favour whoever is listed first.
- **Scores are private;** the "it touched your code" rule isn't built.

## Open questions

1. **Should velocity also show hours spent helping?** That would make goodwill visible as a group total, without saying who helped, the same treatment as passes. Leaning yes.
2. **Optional rule, "it touched your code"** (for W4). Each bug has a 1-in-3 chance of being caused by a colleague's code, and the finder is told whose. Passing it to that colleague is fair routing (it still costs them 2 hours). The receiver isn't told whether it really was their code, so "Dee keeps sending me bugs" could be fair or dumping. The truth goes to the log, for judgement accuracy.
3. **Are scores private?** If they're visible, "dump on the leader" competes with "dump on the one I like least." That could be a second condition.
4. ~~**Event category for a pass.**~~ Settled by ADR 0006: events report their effects, not a category.
5. [**A team changelog**: a public count of bugs each engineer fixed, their own plus those passed to them. It would make good work visible to everyone and give a disliked engineer a visible way to reform, but it partly reveals who passed what.]
