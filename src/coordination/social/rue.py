"""The social layer as a RUE scenario. Everything social is RUE: the mirrored work
state, recorded work events, work judgement, social actions, and social judgement.

The social half of each round is one RUE tick of the scenario's tick plan, as in
reception: the plan, not this class, decides which phases run and in what order.
Conditions are tick plans (stub-social has `full` and `no-judgement`).

A scenario plugs in by providing (see rue-data/stub-social/ and docs/framework.md):

- a predicate for each mirrored piece of work state (for example `points(agent)`);
- a `report_<kind>(actor, target)` predicate for each work event kind, and a phase that
  turns each report into an occurrence its witnesses can judge (`record-work-events`);
- phases whose stages agents choose in. A stage's name is the phase name the Run logs
  ("work-judgement" logs as "work judgement"), and the acting agent is bound as ?SELF
  or ?JUDGE.

Agents are asked only at the stages in `agent_stages`; RUE's ranking decides every
other selection (recording always, and judgement too with `rue_judgement`).
"""

from ..agents import Option
from ..rue_client import RueClient
from ..work import WorkEvent, WorkFact
from .base import Ask

PROMPTS = {
    "work-judgement": "This happened to you in the work. Choose how you judge it.",
    "social-actions": "Between work moves you can say something to a colleague, or say nothing. Choose a social action.",
    "social-judgement": "A colleague told you this. Choose how you judge it.",
}
JUDGEMENT_STAGES = ("work-judgement", "social-judgement")


class RueSocial:
    name = "rue"

    def __init__(self, scenario: str = "stub-social", server: str = "http://localhost:5174",
                 plan: str = "full", rue_judgement: bool = False,
                 agent_stages: tuple[str, ...] = ("work-judgement", "social-actions", "social-judgement")):
        self.rue = RueClient(scenario, server)
        self.plan = plan
        self.agent_stages = [s for s in agent_stages if not (rue_judgement and s in JUDGEMENT_STAGES)]
        self.agents: list[str] = []

    def start(self, agents: list[str], facts: list[str]) -> None:
        self.rue.reset()
        info = self.rue.start(controlled_agents=[], plan=self.plan)
        if set(info["agents"]) != set(agents):
            raise SystemExit(f"The work's agents {sorted(agents)} don't match the RUE scenario's {sorted(info['agents'])}")
        self.agents = list(agents)
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

    def social_round(self, events: list[WorkEvent], ask: Ask) -> None:
        for event in events:
            args = ", ".join(a for a in (event.actor, event.target) if a)
            self.rue.assert_fact(f"report_{event.kind}({args})")
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
