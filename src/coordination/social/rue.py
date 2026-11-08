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
import re

from ..agents import Option, Reason
from ..rue_client import RueClient
from ..work import WorkEvent, WorkFact
from .base import Ask

PROMPTS = {
    "work-judgement": "This happened in the work: {occurrence}. Choose what you call it. A label that names someone says you hold them responsible.",
    "social-actions": "Between work moves you can say something to a colleague, or say nothing. Choose a social action.",
    "social-judgement": "This happened: {occurrence}. Choose how you judge it.",
}

INTRODUCTION = """\
Besides the work, you're part of the group's social life. From time to time you'll be asked to:
- make up your mind about something that happened at work that you know about;
- say something to a colleague, or keep to yourself;
- decide how to take something a colleague said to you.
Each time, you choose from a short list of set options, not free conversation.
Only the person you speak to hears what you say, and you don't learn how they took it.
The options you're offered, and the reasons listed with them, come from a model of your social world: what you've seen your colleagues do, what you've been told, and what you've made of it. They describe how you feel; the choice is yours."""
"""The social world as the agents are told it (ADR 0007): non-normative, and abstract, so
the actions and labels can change without changing what the agents are told."""

MENU_SIZE = 5
"""How many of RUE's top-ranked options an agent is offered at each decision (ADR 0007)."""


class RueSocial:
    name = "rue"
    introduction = INTRODUCTION

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
        self.work_occurrences: set[str] = set()
        for fact in facts:
            self.rue.assert_fact(fact)
        self.rue.set_controlled(self.agents, self.agent_stages)
        self.rue.set_reason_template("reason")

    def briefing(self, agent: str) -> str:
        """The agent's social state (ADR 0007): what it is and how it sees each colleague, not
        the history of what happened (the work Briefing has the work's history, and what
        happened socially has left its mark on the state). RUE renders every sentence with
        the predicates' `state` templates, from the shared world and the agent's own store,
        leaving out neutral values; here they're only grouped: the agent's own traits first,
        then one line per colleague, by name."""
        facts = (self.rue.render_facts("state", skip_defaults=True)
                 + self.rue.render_facts("state", owner=agent, skip_defaults=True))
        own, about = [], {}
        for fact in facts:
            others = [a for a in fact["args"] if a in self.agents and a != agent]
            if others:
                about.setdefault(others[0], []).append(fact["text"])
            else:
                own.append(fact["text"])
        lines = ["Your social world:"] if own or about else []
        if own:
            lines.append("You: " + " ".join(own))
        lines += [f"About {other}: " + " ".join(texts) for other, texts in sorted(about.items())]
        return "\n".join(lines)

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
        public = set(event.witnesses) == set(self.agents)
        # Leaving the actor out of `witnessed` would name it, so that's only done when it's credited.
        judges = event.witnesses if event.credit == "none" else [w for w in event.witnesses if w != event.actor]
        changes = [f'change(?occ, {agent}, "{quantity}") = {value:g}'
                   for agent, quantities in event.changes.items() for quantity, value in quantities.items()]
        changes += [f'sharedChange(?occ, "{quantity}") = {value:g}' for quantity, value in event.shared_changes.items()]
        # Roles: the target, and the actor only when someone is credited. Like every other fact
        # about a partly-witnessed event, they're recorded only for its witnesses (`knownBy`).
        roles = {"TARGET": event.target} if event.target else {}
        if event.credit != "none" and event.actor:
            roles["ACTOR"] = event.actor
        if public:
            effects = ["work_occurrence(?occ)"] + [f"witnessed(?occ, {w})" for w in judges] + changes
        else:
            effects = [f"{w}.work_occurrence(?occ)" for w in event.witnesses]
            effects += [f"{w}.witnessed(?occ, {w})" for w in judges]
            effects += [f"{w}.{change}" for w in event.witnesses for change in changes]
        if event.credit == "public":
            effects.append(f"responsible(?occ, {event.actor})")
        elif event.credit == "witnesses":
            effects += [f"{w}.responsible(?occ, {event.actor})" for w in event.witnesses if w != event.actor]
        occurrence = self.rue.external(
            event.kind, roles, effects, knownBy=None if public else list(event.witnesses),
            text=event.describe(), source="work",
            ref=f"round-{round_number}" if round_number is not None else None,
            data={"kind": event.kind, "details": event.details})
        self.occurrences[occurrence] = event.describe()
        self.work_occurrences.add(occurrence)
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
            for c in candidates:
                c["label"] = self.describe(c["label"])
            options = [Option(id=i, label=c["label"], score=c["score"], is_default=c["isDefault"],
                              reasons=[Reason(text=r["text"], direction=r["direction"]) for r in self.relevant(c)])
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

    def describe(self, label: str) -> str:
        """A candidate's label with any occurrence it names (an id like `occ12`, as RUE renders
        an occurrence-typed role) replaced by that occurrence's text in quotes."""
        return re.sub(r"\bocc\d+\b", lambda m: f'"{self.occurrences[m[0]]}"' if m[0] in self.occurrences else m[0], label)

    def relevant(self, candidate: dict) -> list[dict]:
        """The candidate's reasons that are about the people in it (ADR 0007): a reason shows
        when its fact is about the occurrence being judged, or when every agent it names is
        the one choosing or someone the option names (a fact about some other occurrence
        must name one of them: an old verdict names no one, so it doesn't show). A reason about anyone else (an
        impulse like charitable is about the agent alone, so whatever moved it reaches every
        option that reads it) is left off the menu; the option's ranking is unchanged."""
        bound = {str(v) for v in candidate.get("binding", {}).values()}
        people = bound & set(self.agents)
        def keep(reason: dict) -> bool:
            args = [str(a) for a in reason["fact"]["args"]]
            named = {a for a in args if a in self.agents}
            if set(args) & bound - people:            # about the occurrence being judged
                return True
            if any(a in self.occurrences for a in args):  # about some other occurrence:
                return bool(named) and named <= people    # only if it names the option's people
            return named <= people
        # One reason per occurrence and direction: a rule can read several facts about the
        # same occurrence (what was said, who said it, that you heard it), and each would
        # otherwise restate it on the menu.
        kept, seen = [], set()
        for reason in candidate.get("reasons", []):
            if not keep(reason):
                continue
            first = str(reason["fact"]["args"][0]) if reason["fact"]["args"] else ""
            if first.startswith("occ"):
                if (first, reason.get("direction")) in seen:
                    continue
                seen.add((first, reason.get("direction")))
            kept.append(reason)
        return kept

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
        """Every occurrence RUE has minted that isn't a registered work event. Social occurrences
        are recorded only in their two participants' stores, so this reads RUE's occurrence
        entities rather than querying the shared world."""
        return set(self.rue.entities("occurrence")) - set(self.work_occurrences)
