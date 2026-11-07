"""The social layer as a RUE scenario. Everything social is RUE: the mirrored work
state, recorded work events, work judgement, social actions, and social judgement.

The social half of each round is one RUE tick of the scenario's tick plan, as in
reception: the plan, not this class, decides which phases run and in what order.
Conditions are tick plans (social-layer-data has `full`).

A scenario plugs in by providing (see rue-data/social-layer-data/ and docs/framework.md):

- a predicate for each mirrored piece of work state (for example `points(agent)`);
- the predicates each work event is registered with (see `register` and ADR 0006):
  `work_occurrence(occurrence)`, `witnessed(occurrence, agent)`, the numeric
  `change(occurrence, agent, quantity)`, and `responsible(occurrence, agent)` declared
  with `"privateFallback": "world-first"`, so `?A.responsible(...)` finds public credit,
  credit A witnessed, and credit A assigned itself in work judgement;
- phases whose stages agents choose in. A stage's name is the phase name the Run logs
  ("work-judgement" logs as "work judgement"), and the acting agent is bound as ?SELF
  or ?JUDGE.

Each work event reaches RUE as an external action (RUE's docs/actions.md#external-actions)
before the tick runs, so the tick plan's judgement phases find it as an occurrence.

Agents are asked at the stages in `agent_stages` (by default every one: work judgement,
social actions, social judgement); RUE's ranking decides any other selection.
"""

from ..agents import Option
from ..rue_client import RueClient
from ..work import WorkEvent, WorkFact
from .base import Ask

PROMPTS = {
    "work-judgement": "This happened in the work. Choose what you call it. A label that names someone says you hold them responsible.",
    "social-actions": "Between work moves you can say something to a colleague, or say nothing. Choose a social action.",
    "social-judgement": "A colleague told you this. Choose how you judge it.",
}


class RueSocial:
    name = "rue"

    def __init__(self, scenario: str = "social-layer-data", server: str = "http://localhost:5174",
                 plan: str = "full",
                 agent_stages: tuple[str, ...] = ("work-judgement", "social-actions", "social-judgement")):
        self.rue = RueClient(scenario, server)
        self.plan = plan
        self.agent_stages = list(agent_stages)
        self.agents: list[str] = []
        self.round_number = 0

    def start(self, agents: list[str], facts: list[str]) -> None:
        self.rue.reset()
        info = self.rue.start(controlled_agents=[], plan=self.plan)
        if set(info["agents"]) != set(agents):
            raise SystemExit(f"The work's agents {sorted(agents)} don't match the RUE scenario's {sorted(info['agents'])}")
        self.agents = list(agents)
        self.round_number = 0
        for fact in facts:
            self.rue.assert_fact(fact)
        self.rue.set_controlled(self.agents, self.agent_stages)

    def briefing(self, agent: str) -> str:
        return "\n".join(f"- {text}" for text in sorted(self.rue.render("briefing", owner=agent)))

    def mirror(self, state: list[WorkFact]) -> None:
        for fact in state:
            atom = f"{fact.name}({', '.join(fact.args)})"
            if isinstance(fact.value, bool):
                self.rue.assert_fact(atom if fact.value else f"not {atom}")
            else:
                self.rue.assert_fact(f"{atom} = {fact.value:g}")

    def register(self, event: WorkEvent, round_number: int | None = None) -> str:
        """Register one work event as an external action and return its occurrence (ADR 0006).
        The work's own kind is the actionType, a label no rule matches on. The effects say who
        knows it happened (`witnessed`; not a credited actor, who can't judge its own move), what
        changed (`change`, by agent and quantity), and who is credited with it, as far as
        anyone can see: `responsible` in the world when the credit is public, in each witness's
        own store when only the witnesses know, and nowhere when nobody does. With no credit,
        the actor never reaches RUE: not as a role, a fact, or in the text."""
        effects = ["work_occurrence(?occ)"]
        # Leaving the actor out of `witnessed` would name it, so that's only done when it's credited.
        judges = event.witnesses if event.credit == "none" else [w for w in event.witnesses if w != event.actor]
        effects += [f"witnessed(?occ, {w})" for w in judges]
        effects += [f'change(?occ, {agent}, "{quantity}") = {value:g}'
                    for agent, quantities in event.changes.items() for quantity, value in quantities.items()]
        if event.credit == "public":
            effects.append(f"responsible(?occ, {event.actor})")
        elif event.credit == "witnesses":
            effects += [f"{w}.responsible(?occ, {event.actor})" for w in event.witnesses if w != event.actor]
        return self.rue.external(
            event.kind, {}, effects,
            text=event.describe(), source="work",
            ref=f"round-{round_number}" if round_number is not None else None,
            data={"kind": event.kind, "details": event.details})

    def social_round(self, events: list[WorkEvent], ask: Ask) -> None:
        self.round_number += 1
        for event in events:
            self.register(event, self.round_number)
        result = self.rue.step()
        while result["status"] == "awaiting-choice":
            pending = result["request"]
            binding = pending["binding"]
            agent = binding.get("SELF") or binding.get("JUDGE")
            stage = pending["stageNames"][0]
            candidates = [c for c in pending["candidates"] if not c["belowFloor"]]
            options = [Option(id=c["index"], label=c["label"], score=c["score"], is_default=c["isDefault"])
                       for c in candidates]
            decision = ask(agent, stage.replace("-", " "), PROMPTS.get(stage, "Choose one."), options)
            result = self.rue.choose([] if decision.passed else [decision.choice_id], decision.rue_chooser())
