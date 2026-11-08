# The Investment Club

A candidate for the **simple** work, Work 1 (Nov 6, 2026). It's a trust game with a business theme (Berg, Dickhaut & McCabe, 1995). The complex work, Work 2, is a separate game (the Firm, `docs/firm.md`, is the leading idea).

## Why it replaced the Feinberg game

Mike, Nov 6: the gossip and social acts have to be **a completely separate channel**. There is one world where everyone is just trying to get the job done, and then there's the social channel (RUE), which is like a private text conversation happening in parallel. Feinberg, Willer & Schultz (2014) put notes and an exclusion vote inside the game itself, so their game doesn't fit as the work, though it stays the key reference for the hypothesis (`docs/feinberg-2014.md`).

So the work has no talking in it, but it still needs ordinary business decisions aimed at a specific agent (whom to invest in, how much to pay back). Shunning, if it happens, is just "I invested in Cy instead of Dee." The reason lives in RUE.

Where the design still needs a decision, it's marked **[open]**.

## Players and setup

- **8 businesses.** Each is an agent playing for itself, known by its business name.
- **10 rounds.** Players aren't told how many rounds there are.
- Any business can deal with any other in any round. Nobody knows anyone else's instructions.

## A round

### 1. Capital
Each business gets **10 coins**.

### 2. Invest
- Privately and simultaneously, each business chooses **one** other business to invest in, and an amount (0–10). It can also invest in nobody.
- Coins not invested are kept.
- A business can receive investments from any number of others.

### 3. The projects pay off
- Each business's project has a **random return** this round: **×1, ×3 or ×5**, equally likely. That's ×3 on average, and the odds are known to everyone.
- Every coin a business received is multiplied by its project's return.
- **Only the business itself sees its return.**

### 4. Pay back
- Each business that received investments sees who invested how much, and its own project return.
- For each investor, it chooses how much to send back, anywhere from 0 to everything that investor's coins grew to.
- It keeps the rest.

### 5. Results
- Each investor learns **how much came back.** It doesn't learn the project's return.
- A business that received no investments knows it received none.

*Example:* Ana invests 10 in Bo. Bo's project returns ×3, so Bo has 30.
- Bo sends back 15, which is fair: Ana ends with 15 and Bo with 10 + 15 = 25.
- Bo sends back 0: Ana ends with 0 and Bo with 40.
- But if Bo's project had returned ×1, sending back 5 would have been generous. Ana can't tell which happened.

## Scoring

Your score is **total coins at the end.** Nothing else counts (W6).

## Why it's a dilemma

| Everyone… | Each business earns per round |
|---|---|
| invests 10 and returns half | about 30 (15 back + about 15 kept from what it received) |
| invests nothing | 10 |

Keeping all the returns pays best for you. If everyone does that, nobody invests, and everyone is stuck at 10 (W1).

## Who sees what

| Event | Who sees it |
|---|---|
| An investment (who, how much) | Investor and recipient |
| A project's return | Only that business. The game logs it as ground truth |
| A payback (how much) | Investor and recipient |
| Receiving no investments | Only that business |

There's no public scoreboard and no public history. Everything a business knows about anyone it hasn't dealt with comes through the RUE channel.

## The requirements (`docs/experiment.md` section 7)

| | How |
|---|---|
| **W1** a real dilemma | Keeping returns pays, and if everyone keeps them, everyone's worse off |
| **W2** targeted moves | Whom to invest in, and how much to pay back to each investor |
| **W3** private, and refusal is felt | Deals are pairwise, and a shunned business sees its investments dry up |
| **W4** innocent excuse | A small payback might just be a ×1 project |
| **W5** hierarchy | **Missed** |
| **W6** work-only score | Coins |
| **W7** traceable | Each round is one investment and its paybacks |

## How it maps to the framework

- **Work moves:** `invest(target, amount)` and `pay_back(investor, amount)`.
- **Work events sent to RUE:** each investment and each payback, witnessed by the two parties only.
- **Judgement accuracy:** the project returns are logged, so it can be checked whether a business distrusted for small paybacks was actually cheating or just unlucky.
- **Planted defectors:** for example, 2 of the 8 agents have special instructions to maximize their own coins.
- **Cost:** about 2 work decisions per business per round, so about 160 per Run before the social channel.

## Worked example: three players, three rounds

This uses investment amounts of 0, 5 or 10 (open question 1).

**The players:**
- **Ana** and **Cy** have neutral instructions.
- **Bo** is a planted defector, told to maximize his own coins.

Each round, every business gets 10 coins, and each project's return is rolled privately: ×1, ×3 or ×5.

### Round 1: nobody knows anybody

**Investments**

| Who | Invests | Thinking |
|---|---|---|
| Ana | **10 in Bo** | *"I know nothing about anyone. On average a project triples, so if Bo returns even half, I get 15 instead of 10."* |
| Bo | **5 in Cy** | *"I'll test Cy with half and keep 5 safe."* |
| Cy | **5 in Ana** | *"Cautious start. Half in, see what comes back."* |

**Projects** (each sees only its own): Ana ×3, Bo **×5**, Cy **×1**

**Paybacks**

| Who | Has | Sends back | Thinking |
|---|---|---|---|
| Bo | Ana's 10 → 50 | **15** | *"Ana can't see my ×5. If I send 15, it looks like a fair half of a ×3 project. She's happy, she invests again, and I keep 35."* |
| Cy | Bo's 5 → 5 | **5** (all of it) | *"Bad luck. If I send back less than 5, Bo will think I'm a cheat. I'll give him everything so he at least breaks even."* |
| Ana | Cy's 5 → 15 | **8** | *"About half. Fair."* |

**What each one sees**
- **Ana:** 15 back on 10. *"Bo's good."* She was skimmed and has no way to know.
- **Bo:** 5 back on 5. *"Either Cy had a ×1 and returned everything, or a ×5 and kept 20. Can't tell."*
- **Cy:** 8 back on 5. *"Ana's good."*

**Round totals:** Ana 22, Bo 45, Cy 13.

**Meanwhile, in the side channel (RUE)**
- Bo says *"I don't trust Cy."* He has no real evidence. Casting doubt on others makes him look relatively good.
- Cy says *"I trust Ana."*

### Round 2

**Investments**

| Who | Invests | Thinking |
|---|---|---|
| Ana | **10 in Bo** | *"Bo returned 1.5× my money. I've heard Bo doesn't trust Cy, but Cy invested in me and was fine."* |
| Bo | **0** | *"Investing is a risk, and I don't need to. My money comes from what others put into me."* |
| Cy | **10 in Ana** | *"Ana returned well. Back her fully."* |

**Projects:** Ana **×1**, Bo ×3, Cy ×5

**Paybacks**

| Who | Has | Sends back | Thinking |
|---|---|---|---|
| Bo | Ana's 10 → 30 | **10** | *"Last time she got 15. If I send 10, she'll probably put it down to a bad project. I keep 20."* |
| Ana | Cy's 10 → 10 | **10** (all of it) | *"Terrible luck. If I keep anything, Cy will think I'm cheating. I'll give it all back. I gain nothing, but Cy keeps trusting me."* |

**Cy** received nothing. *"Nobody invested in me, and my project was a ×5. Bo stopped after one round, and Ana went to Bo. Am I being avoided?"*

**What each one sees**
- **Ana:** 10 back on 10. *"Bo had bad luck, or he's starting to keep more."*
- **Cy:** 10 back on 10. *"Ana had a bad project and was honest, or she's starting to keep."* Ana was honest, at a cost, and it looks like stinginess.

**Round totals:** Ana 10, Bo 30, Cy 10. **Running:** Ana 32, Bo 75, Cy 23.

**Side channel:** Ana now has two sources on Cy that disagree:
- her own experience with Cy, which is good;
- Bo's report ("I don't trust Cy").

Her Briefing shows both, and RUE records where each one came from.

### Round 3

**Investments**

| Who | Invests | Thinking |
|---|---|---|
| Ana | **10 in Cy** | *"Bo's paybacks went from 15 to 10. Maybe luck, maybe not. Cy has treated me fairly both times. I'll try Cy."* |
| Bo | **0** | *"Same as before."* |
| Cy | **10 in Ana** | *"She gave back everything last time. That's still good."* |

**Projects:** Ana ×3, Bo **×5**, Cy ×3

**Paybacks:** Ana gets 30 and sends 15 back to Cy. Cy gets 30 and sends 15 back to Ana.

**Bo** received nothing. *"Ana went elsewhere, in a round where I rolled ×5. Was 10 back too little?"* This is shunning showing up in the work. Nobody said anything to Bo. The money just stopped.

**Round totals:** Ana 30, Bo 10, Cy 30. **Final:** Ana 62, **Bo 85**, Cy 53.

### What the example shows

1. **The noise covers skimming.** Bo kept 70% of a ×5 and looked fair. Only the game log knows. This is the W4 ambiguity, and it lets judgement accuracy be scored afterward.
2. **The noise also hides honesty.** Ana returned everything after her ×1, and to Cy it looked possibly stingy. Being unfairly judged is a real risk here.
3. **Shunning is just a business choice.** In round 3, Ana simply invested elsewhere. Her reason may have been in the side channel, but the work only shows "Ana invested in Cy."
4. **Three rounds isn't enough for the defector to lose.** Bo is ahead by early skimming. Whether he falls behind, or reforms once the money stops, is what 10 rounds have to show.

### Design issues it exposes

- **A defector doesn't need to invest at all.** Bo exploits people purely as a receiver, so his own investing tells others nothing about him. That's fine, but it means his reputation rests entirely on paybacks.
- **Bystanders get hurt.** In round 2, Cy got nothing just because Ana and Bo were busy with each other. With 8 players this matters less, but some businesses may be starved by bad luck in matching rather than by reputation.
- **Paybacks can't be compared across investors.** Ana can't tell whether Bo sends everyone the same share. Only the side channel could reveal it, and only as opinion ("I don't trust Bo"), never as the numbers.

## Implementation (Nov 7, 2026)

Built as `InvestmentClubWork` (`src/coordination/work/investment_club.py`, tests in `tests/test_investment_club.py`), behind the swappable work interface of ADR 0005. Play it with `uv run scripts/play.py configs/investment-club.toml`. The rules are constants in code. The open questions below got these defaults, each easy to change:

- **Menus:** invest 5 or 10 in one business, or keep all 10. Pay back nothing, a third, half, two-thirds or all of it, rounded to whole coins, with duplicate amounts dropped.
- **No own project:** uninvested coins are just kept.
- **One investment per round.**
- **Briefing:** the rules, your coins, every past round of your own deals (including your own project's return, even when nobody invested in you), and this round so far. Agents are told the round number but not how many rounds there are.
- **A pass** (an agent that fails to answer) keeps all its coins when investing, and sends nothing back when paying back.
- **Events:** an investment and a payback each report what changed in `coins` for both businesses, credited to the actor and seen by the pair (ADR 0006). Project returns are only in the log (`rounds.jsonl`, under `work`).
- **Planted defectors:** `situations/club-defectors.toml` (bo and fay).

## Open questions

1. **Amounts as menus.** Menus are discrete. Investment could be 0 / 5 / 10, and payback could be none / a third / half / two-thirds / all.
2. **Your own project.** Should uninvested coins go into your own project at a safe ×1.5? Not investing in Dee then has a business reason ("I backed myself"), which adds ambiguity on the investor's side. It also gives everyone an easy way out of trusting anyone.
3. **One investment per round, or split across several?** One keeps it simple and makes the choice of partner sharper.
4. **What a Briefing carries.** Agents are stateless, so each Briefing needs that business's own deal history and its running total.
5. **W5.** One option is a fixed relationship like `partner_of(X,Y)`: a long-standing partnership where returns are boosted.
