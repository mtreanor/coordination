"""The social layer as a RUE scenario. Everything social is RUE: the mirrored work
state, recorded work events, work judgement, social actions, and social judgement.

A scenario plugs in by providing (see rue-data/stub-social/ and docs/framework.md):

- a predicate for each mirrored piece of work state (for example `points(agent)`);
- `report_<kind>(actor, target)` predicates and a `record-work-events` actionGraph whose
  actions turn each report into an occurrence its witnesses can judge. Runs unasked;
- `work-judgement` and `social-judgement` actionGraphs of judgement actions, with roles
  ?JUDGE and ?OCC, looped over every (judge, occurrence) pair;
- a `social-actions` actionGraph with role ?SELF, run for up to `social_passes` passes
  and ending early when everyone picks `stay quiet`.

The Briefing renders each predicate's `briefing` template from the agent's own private
store. Agents pick at every RUE selection, unless `llm_judgement` is off (RUE's ranking
picks the judgement actions) or `judgement` is off (no judgement phases at all).
"""

from ..agents import Option
from ..rue_client import RueClient
from ..work import WorkEvent, WorkFact
from .base import Ask

PROMPTS = {
    "work judgement": "This happened to you in the work. Choose how you judge it.",
    "social actions": "Between work moves you can say something to a colleague, or say nothing. Choose a social action.",
    "social judgement": "A colleague told you this. Choose how you judge it.",
}


class RueSocial:
    name = "rue"

    def __init__(self, scenario: str = "stub-social", server: str = "http://localhost:5174",
                 social_passes: int = 2, judgement: bool = True, llm_judgement: bool = True,
                 quiet_action: str = "stay quiet"):
        self.rue = RueClient(scenario, server)
        self.social_passes = social_passes
        self.judgement = judgement
        self.llm_judgement = llm_judgement
        self.quiet_action = quiet_action
        self.agents: list[str] = []

    def start(self, agents: list[str], facts: list[str]) -> None:
        self.rue.reset()
        info = self.rue.start(controlled_agents=[])
        if set(info["agents"]) != set(agents):
            raise SystemExit(f"The work's agents {sorted(agents)} don't match the RUE scenario's {sorted(info['agents'])}")
        self.agents = list(agents)
        for fact in facts:
            self.rue.assert_fact(fact)

    def briefing(self, agent: str) -> str:
        return "\n".join(f"- {text}" for text in sorted(self.rue.render("briefing", owner=agent)))

    def mirror(self, state: list[WorkFact]) -> None:
        for fact in state:
            atom = f"{fact.name}({', '.join(fact.args)})"
            if isinstance(fact.value, bool):
                self.rue.assert_fact(atom if fact.value else f"not {atom}")
            else:
                self.rue.assert_fact(f"{atom} = {fact.value:g}")

    def record(self, events: list[WorkEvent]) -> None:
        for event in events:
            args = ", ".join(a for a in (event.actor, event.target) if a)
            self.rue.assert_fact(f"report_{event.kind}({args})")
        self._phase("record work events", "record-work-events", [], ask=None)

    def work_judgement(self, ask: Ask) -> None:
        if self.judgement:
            self._phase("work judgement", "work-judgement", ["JUDGE", "OCC"], ask if self.llm_judgement else None)

    def social_actions(self, ask: Ask) -> None:
        for _ in range(self.social_passes):
            taken = self._phase("social actions", "social-actions", ["SELF"], ask)
            if all(action in (None, self.quiet_action) for action in taken):
                break

    def social_judgement(self, ask: Ask) -> None:
        if self.judgement:
            self._phase("social judgement", "social-judgement", ["JUDGE", "OCC"], ask if self.llm_judgement else None)

    def _phase(self, phase: str, graph: str, loop: list[str], ask: Ask | None) -> list[str | None]:
        """Run one RUE tick of one actionGraph. With `ask`, every selection is put to the
        agent making it; without, RUE's ranking decides. Returns the chosen action names."""
        self.rue.set_plan([{"actionGraph": graph, "loop": loop}])
        self.rue.set_controlled(self.agents if ask else [])
        chosen: list[str | None] = []
        result = self.rue.step()
        while result["status"] == "awaiting-choice":
            pending = result["request"]
            binding = pending["binding"]
            agent = binding.get("SELF") or binding.get("JUDGE")
            candidates = [c for c in pending["candidates"] if not c["belowFloor"]]
            options = [Option(id=c["index"], label=c["label"], score=c["score"], is_default=c["isDefault"])
                       for c in candidates]
            decision = ask(agent, phase, PROMPTS[phase], options)
            by_index = {c["index"]: c for c in candidates}
            chosen.append(None if decision.passed else by_index[decision.choice_id]["actionName"])
            result = self.rue.choose([] if decision.passed else [decision.choice_id], decision.rue_chooser())
        return chosen
