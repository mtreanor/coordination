"""Not My Bug: whom do you hurt, and whom do you help? (docs/not-my-bug.md)

Each round (sprint) every engineer has 10 hours and finds one bug in their own code.
At the same time as the others, each one:

- fixes it: 1 hour;
- passes it to a colleague: free for them, 2 hours for the colleague (unfamiliar code);
- fixes it and helps a colleague: 2 hours, and the colleague is spared 1 hour of
  whatever they have to fix this round.

Every bug passed to you must be fixed (2 hours each, less any help). The score is the
hours left for your own work. Only the two people involved know about a pass or a help;
everyone sees the team's velocity, which counts the hours lost to handoffs exactly but
not who caused them. A round is one step.
"""

import random

from ..agents import Option
from .base import WorkDecision, WorkEvent, WorkFact

ROUNDS = 8
HOURS = 10
OWN_FIX = 1
PASSED_FIX = 2
HELP = 1

RULES = f"""\
You're an engineer on a software team. Your score is the hours you have left for your own work (the features you ship), summed over every sprint.
Each sprint you have {HOURS} hours and find one bug in your own code. At the same time as your colleagues, you choose one:
- Fix it yourself: {OWN_FIX} hour.
- Pass it to a colleague: it costs you nothing, but it costs them {PASSED_FIX} hours, because it's code they don't know.
- Fix it yourself and help a colleague: {OWN_FIX + HELP} hours in all, and that colleague is spared {HELP} hour of whatever they have to fix this sprint.
Every bug passed to you must be fixed ({PASSED_FIX} hours each, less any help). You can't pass it on.
Only the two people involved know about a pass or a help. After each sprint everyone sees the team's velocity: how many hours the whole team shipped, how many were lost to handoffs, and how many went to helping."""

INTRODUCTION = """\
You're engineers on a software team. Each sprint, everyone ships features and fixes bugs. Bugs can be fixed yourself, passed to a colleague, or fixed while helping someone else, and each choice costs hours someone could have spent shipping. Before each sprint's decision you'll be given the details: the rules, your sprints so far, and the team's velocity."""

PROMPT = "Choose what to do with your bug this sprint."


class NotMyBugWork:
    name = "not-my-bug"
    introduction = INTRODUCTION
    default_agents = ["ana", "bo", "cy", "dee", "eli"]

    def __init__(self, agents: list[str] | None = None, seed: int = 0, rounds: int | None = None):
        self.agents = list(agents or self.default_agents)
        if len(self.agents) < 2:
            raise ValueError("Not My Bug needs at least two engineers")
        self.rounds = rounds or ROUNDS
        self.menu_rng = random.Random(f"{seed}-menus")  # LLMs favour whoever is listed first
        self.round = 0
        self.pending = False
        self.hours = {agent: 0 for agent in self.agents}
        self.history: dict[str, list[str]] = {agent: [] for agent in self.agents}
        self.velocity: list[str] = []
        self._menus: dict[str, list[tuple[str, str | None]]] = {}
        self._record: dict = {}

    def next_round(self) -> None:
        self.round += 1
        self.pending = True

    def decisions(self) -> list[WorkDecision]:
        if not self.pending:
            return []
        return [self._decision(agent) for agent in self.agents]

    def _decision(self, agent: str) -> WorkDecision:
        others = [other for other in self.agents if other != agent]
        self.menu_rng.shuffle(others)
        menu = [("fix", None)] + [("pass", o) for o in others] + [("help", o) for o in others]
        self._menus[agent] = menu
        # The hours are on the menu: without them, models misread which move pays (a Nov 7 pilot).
        # These costs leave out bugs passed to you, which cost 2 hours each on top.
        labels = {
            "fix": f"Fix your bug yourself (it costs you {OWN_FIX} hour)",
            "pass": f"Pass your bug to {{}} (it costs you nothing; it costs {{}} {PASSED_FIX} hours)",
            "help": f"Fix your bug yourself and help {{}} (it costs you {OWN_FIX + HELP} hours; it spares {{}} {HELP} hour)",
        }
        options = [Option(id=i, label=labels[kind].format(target, target)) for i, (kind, target) in enumerate(menu)]
        return WorkDecision(key=agent, agent=agent, prompt=PROMPT, options=options)

    def resolve(self, answers: dict[str, int | None]) -> list[WorkEvent]:
        if not self.pending:
            return []
        moves = {}
        for agent in self.agents:
            choice = answers.get(agent)
            moves[agent] = ("fix", None) if choice is None else self._menus[agent][choice]

        # What each engineer must fix this round, before help.
        workload = {agent: 0 for agent in self.agents}
        passed_to: dict[str, list[str]] = {agent: [] for agent in self.agents}
        for agent, (kind, target) in moves.items():
            if kind == "pass":
                workload[target] += PASSED_FIX
                passed_to[target].append(agent)
            else:
                workload[agent] += OWN_FIX

        # Help spares the target an hour of that workload. Help a colleague who has nothing
        # left to fix isn't needed, and the helper gets the hour back.
        spent = {agent: workload[agent] for agent in self.agents}
        helped_by: dict[str, list[str]] = {agent: [] for agent in self.agents}
        unneeded: list[str] = []
        for agent in self.agents:  # in the work's fixed order, so it's reproducible
            kind, target = moves[agent]
            if kind != "help":
                continue
            if spent[target] >= HELP:
                spent[target] -= HELP
                spent[agent] += HELP
                helped_by[target].append(agent)
            else:
                unneeded.append(agent)

        events: list[WorkEvent] = []
        lines: dict[str, list[str]] = {agent: [] for agent in self.agents}
        for agent in self.agents:
            kind, target = moves[agent]
            if kind == "pass":
                lines[agent].append(f"You passed your bug to {target}. It cost you nothing and cost {target} {PASSED_FIX} hours.")
                events.append(WorkEvent(kind="passed a bug to", actor=agent, target=target, witnesses=[agent, target],
                                        changes={agent: {"hours": OWN_FIX}, target: {"hours": -PASSED_FIX}},
                                        text=f"{agent} passed their bug to {target} in sprint {self.round}"))
            elif kind == "help" and agent in helped_by[target]:
                lines[agent].append(f"You fixed your bug and helped {target}. It cost you {OWN_FIX + HELP} hours and spared {target} {HELP} hour.")
                events.append(WorkEvent(kind="helped with a bug", actor=agent, target=target, witnesses=[agent, target],
                                        changes={agent: {"hours": -HELP}, target: {"hours": HELP}},
                                        text=f"{agent} helped {target} with a bug in sprint {self.round}"))
            elif kind == "help":
                lines[agent].append(f"You fixed your bug and went to help {target}, "
                                    f"but {target} had nothing left to fix, so you got the hour back.")
            else:
                lines[agent].append(f"You fixed your bug yourself. It cost you {OWN_FIX} hour."
                                    + (" (You didn't choose.)" if answers.get(agent) is None else ""))
            for passer in passed_to[agent]:
                lines[agent].append(f"{passer} passed their bug to you. It cost you {PASSED_FIX} hours.")
            for helper in helped_by[agent]:
                lines[agent].append(f"{helper} helped you. It spared you {HELP} hour.")

        shipped = {agent: HOURS - spent[agent] for agent in self.agents}
        possible = len(self.agents) * (HOURS - OWN_FIX)
        lost = possible - sum(shipped.values())
        helping = sum(len(h) for h in helped_by.values()) * HELP
        velocity = (f"Team velocity in sprint {self.round}: {sum(shipped.values())} hours shipped of a possible "
                    f"{possible}; {lost} lost to handoffs; {helping} went to helping colleagues.")
        # Everyone sees the velocity, hours lost included, in the work Briefing. It is not a work
        # event: an uncredited loss can be pinned on anyone, and in exp/5-reform-revisited
        # passers blamed the colleague they'd passed to for it every sprint, so the label's
        # effects on feelings kept the passing going (docs/experiments/exp5-reform-revisited.md).
        self.velocity.append(velocity)
        for agent in self.agents:
            self.hours[agent] += shipped[agent]
            self.history[agent].append(f"Sprint {self.round}: " + " ".join(lines[agent])
                                       + f" You shipped {shipped[agent]} hours.")
        self._record = {
            "round": self.round,
            "moves": {agent: {"move": kind, "target": target} for agent, (kind, target) in moves.items()},
            "helped": {target: helpers for target, helpers in helped_by.items() if helpers},
            "unneeded_help": unneeded,
            "shipped": shipped,
            "lost_to_handoffs": lost,
            "hours": dict(self.hours),
        }
        self.pending = False
        return events

    def briefing(self, agent: str) -> str:
        lines = [RULES, "", f"You have shipped {self.hours[agent]} hours so far."]
        if self.history[agent]:
            lines += ["", "Your past sprints:"] + [f"- {line}" for line in self.history[agent]]
            lines += ["", "The team's velocity so far:"] + [f"- {line}" for line in self.velocity]
        if self.pending:
            lines += ["", f"This is sprint {self.round}."]
        return "\n".join(lines)

    def state(self) -> list[WorkFact]:
        return [WorkFact(name="points", args=[agent], value=hours) for agent, hours in self.hours.items()]

    def record(self) -> dict:
        return dict(self._record)

    def over(self) -> bool:
        return self.round >= self.rounds and not self.pending

    def scores(self) -> dict[str, float]:
        return dict(self.hours)
