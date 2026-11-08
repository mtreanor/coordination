"""The Investment Club: a trust game between businesses (docs/investment-club.md).

Each round has two steps:

1. Invest: every business gets 10 coins and, at the same time as the others, invests
   5 or 10 of them in one other business, or keeps them all.
2. Pay back: each business's project multiplies what it received by a random return
   (x1, x3 or x5, equally likely), which only that business sees. For each investor,
   it chooses how much of that investor's grown coins to send back.

The score is total coins. Deals are pairwise and private: an investor learns how much
came back, never the project's return, so a small payback might be bad luck (W4).
Project returns are ground truth for the log only (`record`), never mirrored.
"""

import random

from ..agents import Option
from .base import WorkDecision, WorkEvent, WorkFact

ROUNDS = 10
ENDOWMENT = 10
INVEST_AMOUNTS = (5, 10)
RETURNS = (1, 3, 5)
PAYBACK_SHARES = ((0, "nothing"), (1 / 3, "a third"), (1 / 2, "half"), (2 / 3, "two-thirds"), (1, "all of it"))

RULES = """\
You run a small business in an investment club. Your score is the coins you have at the end.
Each round:
1. Every business gets 10 coins. At the same time as the others, you may invest 5 or 10 of them in one other business's project, or keep them all.
2. Every project then returns x1, x3 or x5 what was invested in it, each equally likely. Only a business sees its own project's return.
3. For each business that invested in you, you choose how much of what their coins grew to you send back. You keep the rest.
Deals are private: only the two businesses involved know about an investment or a payback. An investor learns how much came back, but not what the project returned."""


INTRODUCTION = """\
You each run a small business, and you belong to an investment club together. Each round, members can invest in one another's projects and send back a share of what those investments grew to. Before each decision you'll be given the details: the rules, your coins, and your rounds so far."""


def _round_half_up(x: float) -> int:
    return int(x + 0.5)


class InvestmentClubWork:
    name = "investment-club"
    introduction = INTRODUCTION
    default_agents = ["ana", "bo", "cy", "dee", "eli", "fay", "gus", "hal"]

    def __init__(self, agents: list[str] | None = None, seed: int = 0, rounds: int | None = None):
        self.agents = list(agents or self.default_agents)
        if len(self.agents) < 2:
            raise ValueError("The Investment Club needs at least two businesses")
        self.rounds = rounds or ROUNDS
        self.rng = random.Random(seed)  # project returns
        self.menu_rng = random.Random(f"{seed}-menus")  # menu order, kept apart so it can't change the dice
        self.round = 0
        self.step: str | None = None  # "invest", "payback", or None between rounds
        self.coins = {agent: 0 for agent in self.agents}
        self.history: dict[str, list[str]] = {agent: [] for agent in self.agents}
        self._menus: dict[str, list] = {}
        self._record: dict = {}
        self._new_round_state()

    def _new_round_state(self) -> None:
        self.returns: dict[str, int] = {}
        self.investments: dict[str, tuple[str, int]] = {}  # investor -> (recipient, amount)
        self.paybacks: dict[tuple[str, str], int] = {}  # (recipient, investor) -> coins sent back
        self.today: dict[str, list[str]] = {agent: [] for agent in self.agents}
        self.start_coins = dict(self.coins)

    # Rounds and steps

    def next_round(self) -> None:
        self.round += 1
        self._new_round_state()
        self.returns = {agent: self.rng.choice(RETURNS) for agent in self.agents}
        self.step = "invest"

    def decisions(self) -> list[WorkDecision]:
        self._menus = {}
        if self.step == "invest":
            return [self._invest_decision(agent) for agent in self.agents]
        if self.step == "payback":
            return [self._payback_decision(recipient, investor)
                    for investor, (recipient, _) in sorted(self.investments.items(), key=lambda kv: (kv[1][0], kv[0]))]
        return []

    def _invest_decision(self, agent: str) -> WorkDecision:
        key = f"invest:{agent}"
        # The businesses are listed in a fresh random order for each agent each round: in a
        # fixed order, LLM agents invest in whoever is listed first (a Nov 7 pilot Run).
        others = [other for other in self.agents if other != agent]
        self.menu_rng.shuffle(others)
        menu: list[tuple[str | None, int]] = [(None, 0)]
        menu += [(other, amount) for other in others for amount in INVEST_AMOUNTS]
        self._menus[key] = menu
        options = [Option(id=i, label=f"Keep all {ENDOWMENT} coins" if target is None
                          else f"Invest {amount} coins in {target}")
                   for i, (target, amount) in enumerate(menu)]
        return WorkDecision(key=key, agent=agent, options=options,
                            prompt=f"You have {ENDOWMENT} coins to invest this round. Choose your investment.")

    def _payback_decision(self, recipient: str, investor: str) -> WorkDecision:
        key = f"payback:{recipient}:{investor}"
        amount = self.investments[investor][1]
        grown = amount * self.returns[recipient]
        backs: list[int] = []
        for share, _ in PAYBACK_SHARES:
            back = _round_half_up(grown * share)
            if back not in backs:
                backs.append(back)
        self._menus[key] = backs
        names = {_round_half_up(grown * share): name for share, name in reversed(PAYBACK_SHARES)}
        options = [Option(id=i, label=f"Send back {back} coins to {investor} ({names[back]})")
                   for i, back in enumerate(backs)]
        return WorkDecision(key=key, agent=recipient, options=options,
                            prompt=f"{investor} invested {amount} coins in you, and your project returned "
                                   f"x{self.returns[recipient]}, so they grew to {grown}. "
                                   f"Choose how much to send back to {investor}.")

    def resolve(self, answers: dict[str, int | None]) -> list[WorkEvent]:
        if self.step == "invest":
            return self._resolve_invest(answers)
        if self.step == "payback":
            return self._resolve_payback(answers)
        return []

    def _resolve_invest(self, answers: dict[str, int | None]) -> list[WorkEvent]:
        events = []
        for agent in self.agents:
            choice = answers.get(f"invest:{agent}")
            target, amount = (None, 0) if choice is None else self._menus[f"invest:{agent}"][choice]
            self.coins[agent] += ENDOWMENT - amount
            if target is None:
                self.today[agent].append(f"You kept all {ENDOWMENT} coins."
                                         + (" (You didn't choose.)" if choice is None else ""))
                continue
            self.investments[agent] = (target, amount)
            self.today[agent].append(f"You invested {amount} coins in {target} and kept {ENDOWMENT - amount}.")
            events.append(WorkEvent(kind="invested in", actor=agent, target=target, witnesses=[agent, target],
                                    changes={agent: {"coins": -amount}, target: {"coins": amount}},
                                    details={"amount": amount},
                                    text=f"{agent} invested {amount} coins in {target} in round {self.round}"))
        for agent in self.agents:
            received = [(investor, amount) for investor, (recipient, amount) in self.investments.items()
                        if recipient == agent]
            if received:
                total = sum(amount for _, amount in received)
                listing = ", ".join(f"{investor} {amount}" for investor, amount in sorted(received))
                self.today[agent].append(
                    f"Investments in you: {listing}. Your project returned x{self.returns[agent]}, "
                    f"so they grew to {total * self.returns[agent]} coins.")
            else:
                self.today[agent].append(
                    f"Nobody invested in you. (Your project would have returned x{self.returns[agent]}.)")
        self.step = "payback" if self.investments else None
        if self.step is None:
            self._end_round()
        return events

    def _resolve_payback(self, answers: dict[str, int | None]) -> list[WorkEvent]:
        events = []
        for investor, (recipient, amount) in sorted(self.investments.items()):
            key = f"payback:{recipient}:{investor}"
            choice = answers.get(key)
            grown = amount * self.returns[recipient]
            back = 0 if choice is None else self._menus[key][choice]
            self.paybacks[(recipient, investor)] = back
            self.coins[investor] += back
            self.coins[recipient] += grown - back
            self.today[recipient].append(
                f"You sent back {back} of {grown} coins to {investor} and kept {grown - back}."
                + (" (You didn't choose, so nothing was sent.)" if choice is None else ""))
            self.today[investor].append(f"{recipient} sent back {back} coins on your {amount}.")
            events.append(WorkEvent(kind="paid back", actor=recipient, target=investor,
                                    witnesses=[recipient, investor],
                                    changes={recipient: {"coins": -back}, investor: {"coins": back}},
                                    details={"amount": back, "stake": amount},
                                    text=f"{recipient} sent back {back} coins to {investor}, "
                                         f"who had invested {amount}, in round {self.round}"))
        self.step = None
        self._end_round()
        return events

    def _end_round(self) -> None:
        for agent in self.agents:
            gained = self.coins[agent] - self.start_coins[agent]
            self.history[agent].append(f"Round {self.round}: " + " ".join(self.today[agent])
                                       + f" You gained {gained} coins.")
        self._record = {
            "round": self.round,
            "returns": dict(self.returns),
            "investments": [{"investor": i, "recipient": r, "amount": a}
                            for i, (r, a) in sorted(self.investments.items())],
            "paybacks": [{"recipient": r, "investor": i, "sent_back": b,
                          "grown": self.investments[i][1] * self.returns[r]}
                         for (r, i), b in sorted(self.paybacks.items())],
            "coins": dict(self.coins),
        }

    # What agents and the social world see

    def briefing(self, agent: str) -> str:
        lines = [RULES, "", f"You have {self.coins[agent]} coins."]
        if self.history[agent]:
            lines += ["", "Your past rounds:"] + [f"- {line}" for line in self.history[agent]]
        if self.step is not None:
            lines += ["", f"This is round {self.round}."]
            if self.today[agent]:
                lines += ["So far this round:"] + [f"- {line}" for line in self.today[agent]]
        return "\n".join(lines)

    def state(self) -> list[WorkFact]:
        return [WorkFact(name="points", args=[agent], value=coins) for agent, coins in self.coins.items()]

    def record(self) -> dict:
        return dict(self._record)

    def over(self) -> bool:
        return self.round >= self.rounds and self.step is None

    def scores(self) -> dict[str, float]:
        return dict(self.coins)
