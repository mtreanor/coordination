"""A thin client for one scenario on the RUE server's Play API (external/rue/docs/server-api.md)."""

import httpx


class RueClient:
    def __init__(self, scenario: str, base_url: str = "http://localhost:5174"):
        self.http = httpx.Client(base_url=f"{base_url}/api/play/{scenario}", timeout=30)

    def _post(self, path: str, body: dict | None = None) -> dict:
        response = self.http.post(path, json=body or {})
        if response.is_error:
            raise RuntimeError(f"POST {path} failed ({response.status_code}): {response.text}")
        return response.json()

    def _get(self, path: str) -> dict:
        response = self.http.get(path)
        if response.is_error:
            raise RuntimeError(f"GET {path} failed ({response.status_code}): {response.text}")
        return response.json()

    def reset(self) -> None:
        self._post("/reset")

    def start(self, controlled_agents: list[str], plan: str | None = None) -> dict:
        """Start a session on the named tick plan (None: the scenario's default)."""
        body = {"controlled": {"agents": controlled_agents, "stages": []}}
        if plan:
            body["planName"] = plan
        return self._post("/start", body)

    def set_controlled(self, agents: list[str], stages: list[str] | None = None) -> None:
        """Which selections pause for an outside choice: those made by these agents, at these
        stages ([] or None: any stage). With no agents and no stages, RUE chooses everything."""
        self._post("/config", {"controlled": {"agents": agents, "stages": stages or []}})

    def set_reason_template(self, template: str) -> None:
        """The text template RUE renders served candidates' reasons with."""
        self._post("/config", {"reasonTemplate": template})

    def set_plan(self, phases: list[dict] | None) -> None:
        """Replace what the next tick runs: [{actionGraph, loop?, bindings?} | {ruleset}], or None
        for the scenario's default tick plan."""
        self._post("/plan", {"plan": phases})

    def step(self) -> dict:
        """Run one tick: {status: tick-complete, ...} or {status: awaiting-choice, request}."""
        return self._post("/step")

    def choose(self, indexes: list[int], chooser: dict) -> dict:
        """Answer the pending choice. chooser is {kind: player|agent, id?, note?}; RUE records it."""
        return self._post("/choose", {"indexes": indexes, "chooser": chooser})

    def external(self, action_type: str, roles: dict | None = None, effects: list[str] | None = None,
                 **context) -> str:
        """Register something that happened outside RUE as an external action and return its
        occurrence id. context: text, source, ref, data."""
        body = {"actionType": action_type, "roles": roles or {}, "effects": effects or [], **context}
        return self._post("/external", body)["occurrence"]

    def assert_fact(self, text: str) -> None:
        self._post("/assert", {"text": text})

    def query(self, text: str) -> dict:
        return self._post("/query", {"text": text})

    def explain(self, name: str, args: list[str], owner: str | None = None) -> dict:
        return self._post("/explain", {"name": name, "args": args, **({"owner": owner} if owner else {})})

    def render(self, template: str, owner: str | None = None, skip_defaults: bool = False) -> list[str]:
        """The text of every active fact whose predicate has the named template, from the
        world store or one entity's private store (RUE's predicate toString templates), in
        the order asserted; with skip_defaults, not numeric facts at their default."""
        return [r["text"] for r in self.render_facts(template, owner, skip_defaults)]

    def render_facts(self, template: str, owner: str | None = None, skip_defaults: bool = False) -> list[dict]:
        """Like render, with each fact: {name, args, value, negated, text}."""
        body = {"template": template, "skipDefaults": skip_defaults, **({"owner": owner} if owner else {})}
        return self._post("/render", body)["rendered"]

    def entities(self, entity_type: str) -> list[str]:
        """The names of every entity of one type in the running session."""
        groups = self._get("/entities")["entities"]
        return next((g["names"] for g in groups if g["type"] == entity_type), [])

    def facts(self) -> list[dict]:
        return self._get("/facts")["facts"]
