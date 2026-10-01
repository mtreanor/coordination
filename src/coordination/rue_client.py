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

    def start(self, controlled_agents: list[str]) -> dict:
        return self._post("/start", {"controlled": {"agents": controlled_agents, "stages": []}})

    def step(self) -> dict:
        """Run one tick: {status: tick-complete, ...} or {status: awaiting-choice, request}."""
        return self._post("/step")

    def choose(self, indexes: list[int], chooser: dict) -> dict:
        """Answer the pending choice. chooser is {kind: player|agent, id?, note?}; RUE records it."""
        return self._post("/choose", {"indexes": indexes, "chooser": chooser})

    def assert_fact(self, text: str) -> None:
        self._post("/assert", {"text": text})

    def query(self, text: str) -> dict:
        return self._post("/query", {"text": text})

    def explain(self, name: str, args: list[str]) -> dict:
        return self._post("/explain", {"name": name, "args": args})

    def facts(self) -> list[dict]:
        return self._get("/facts")["facts"]
