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
  in every stage.

Each work event reaches RUE as an external action (RUE's docs/actions.md#external-actions)
before the tick runs, so the tick plan's judgement phases find it as an occurrence.

Agents are asked at the stages in `agent_stages` (by default every one: work judgement,
social actions, social judgement); RUE's ranking decides any other selection.
"""

import random

from ..agents import Option, Reason
from ..rue_client import RueClient
from ..work import WorkEvent, WorkFact
from .base import Ask

PROMPTS = {
    "work-judgement": "This happened in the work: {occurrence}. Choose what you call it. A label that names someone says you hold them responsible.",
    "social-actions": "Between work moves you can say something to a colleague, or say nothing. Choose a social action.",
    "social-judgement": "This happened: {occurrence}. Choose how you judge it.",
}

MENU_SIZE = 5
"""How many of RUE's top-ranked options an agent is offered at each decision (ADR 0007)."""


class RueSocial:
    name = "rue"

    def __init__(self, scenario: str = "social-layer-data", server: str = "http://localhost:5174",
                 plan: str = "full",
                 agent_stages: tuple[str, ...] = ("work-judgement", "social-actions", "social-judgement"),
                 seed: int = 0, menu_size: int = MENU_SIZE):
        self.rue = RueClient(scenario, server)
        self.menu_size = menu_size
        self.occurrences: dict[str, str] = {}  # occurrence -> its text, for the decisions about it
        self.seed = seed
        self.shuffle = random.Random(seed)
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
        self.shuffle = random.Random(self.seed)
        self.occurrences = {}
        for fact in facts:
            self.rue.assert_fact(fact)
        self.rue.set_controlled(self.agents, self.agent_stages)

    def briefing(self, agent: str) -> str:
        """The agent's RUE state (ADR 0007): the shared world and the agent's own store, each
        in the order it happened, rendered by RUE's `briefing` templates. Neutral values
        (a numeric at its default) are left out. All of the shared world is shown, including
        who knows about what, for now."""
        sections = []
        for heading, owner in (("In the social world:", None), ("What you think:", agent)):
            texts = self.rue.render("briefing", owner=owner, skip_defaults=True)
            if texts:
                sections += [heading] + [f"- {text}" for text in texts]
        return "\n".join(sections)

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
        the actor never reaches RUE: not as a role, a fact, or in the text.

        The shared world holds only what every agent knows. An event every agent witnessed is
        recorded there; one only some witnessed is recorded in each witness's own store
        (`bob.witnessed(occ, bob)`, `bob.change(...)`), so a Briefing, which renders the shared
        world and the agent's own store, never shows an event the agent didn't witness. Rules
        read `?A.witnessed(?O, ?A)`, which finds both (`privateFallback: world-first`)."""
        effects = ["work_occurrence(?occ)"]
        public = set(event.witnesses) == set(self.agents)
        # Leaving the actor out of `witnessed` would name it, so that's only done when it's credited.
        judges = event.witnesses if event.credit == "none" else [w for w in event.witnesses if w != event.actor]
        changes = [f'change(?occ, {agent}, "{quantity}") = {value:g}'
                   for agent, quantities in event.changes.items() for quantity, value in quantities.items()]
        if public:
            effects += [f"witnessed(?occ, {w})" for w in judges] + changes
        else:
            effects += [f"{w}.witnessed(?occ, {w})" for w in judges]
            effects += [f"{w}.{change}" for w in event.witnesses for change in changes]
        if event.credit == "public":
            effects.append(f"responsible(?occ, {event.actor})")
        elif event.credit == "witnesses":
            effects += [f"{w}.responsible(?occ, {event.actor})" for w in event.witnesses if w != event.actor]
        occurrence = self.rue.external(
            event.kind, {}, effects,
            text=event.describe(), source="work",
            ref=f"round-{round_number}" if round_number is not None else None,
            data={"kind": event.kind, "details": event.details})
        self.occurrences[occurrence] = event.describe()
        return occurrence

    def social_round(self, events: list[WorkEvent], ask: Ask) -> None:
        self.round_number += 1
        for event in events:
            self.register(event, self.round_number)
        result = self.rue.step()
        while result["status"] == "awaiting-choice":
            pending = result["request"]
            binding = pending["binding"]
            agent = binding["SELF"]
            stage = pending["stageNames"][0]
            candidates = self.menu([c for c in pending["candidates"] if not c["belowFloor"]])
            options = [Option(id=i, label=c["label"], score=c["score"], is_default=c["isDefault"],
                              reasons=[Reason(text=r["text"], direction=r["direction"]) for r in c.get("reasons", [])])
                       for i, c in enumerate(candidates)]
            prompt = PROMPTS.get(stage, "Choose one.").format(occurrence=self.occurrences.get(binding.get("OCC"), "something"))
            decision = ask(agent, stage.replace("-", " "), prompt, options)
            chosen = [] if decision.passed else [candidates[decision.choice_id]]
            known = self._social_occurrences() if chosen and stage == "social-actions" else None
            result = self.rue.choose([c["index"] for c in chosen], decision.rue_chooser())
            if known is not None:
                # A social action that records an occurrence is described by its own text,
                # which is the option's label; remember it for the listener's judgement.
                for occurrence in self._social_occurrences() - known:
                    self.occurrences[occurrence] = chosen[0]["label"]

    def menu(self, candidates: list[dict]) -> list[dict]:
        """RUE's top-ranked options, at most `menu_size`, in random order (ADR 0007). RUE lists
        candidates best first, with ties in the order the actions are written, and its index
        is the rank; so ties are broken at random, the cut is shown shuffled, and options are
        numbered by position. Neither the order nor the ids give the ranking away. Scores stay
        on the options for the log; agents are never shown them."""
        self.shuffle.shuffle(candidates)
        candidates.sort(key=lambda c: -c["score"])  # stable: equal scores keep the random order
        top = candidates[:self.menu_size]
        self.shuffle.shuffle(top)
        return top

    def _social_occurrences(self) -> set[str]:
        return {row["o"] for row in self.rue.query("social_occurrence(?o)")["rows"]}
