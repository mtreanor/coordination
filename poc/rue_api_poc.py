# /// script
# requires-python = ">=3.11"
# dependencies = ["httpx"]
# ///
"""Proof of concept: drive a RUE play session entirely from Python.

Start the RUE server first (from the repo root):

    cd external/rue/tools/action-rule-set-tool && npm run server

Then:

    uv run poc/rue_api_poc.py                  # Python always takes RUE's top-ranked move
    uv run poc/rue_api_poc.py --policy random  # Python picks at random (seeded)
    uv run poc/rue_api_poc.py --policy ask     # you pick each move at the prompt

Every decision is "controlled": RUE scores the candidates and pauses, and
Python chooses, telling RUE who chose and why (recorded on the ActionRecord). The script also pushes a fact into RUE mid-run (the way the
game will mirror state changes) and asks RUE to explain a fact at the end.
"""

import argparse
import random

import httpx

SCENARIO = "poc"
AGENTS = ["alice", "bob", "carol"]


class RueClient:
    """Thin wrapper over the RUE tool server's play API for one scenario."""

    def __init__(self, base_url: str, scenario: str):
        self.http = httpx.Client(base_url=f"{base_url}/api/play/{scenario}", timeout=30)

    def _post(self, path: str, body: dict | None = None) -> dict:
        response = self.http.post(path, json=body or {})
        if response.is_error:
            raise RuntimeError(f"POST {path} failed ({response.status_code}): {response.text}")
        return response.json()

    def reset(self) -> None:
        self._post("/reset")

    def start(self, controlled_agents: list[str]) -> dict:
        return self._post("/start", {"controlled": {"agents": controlled_agents, "stages": []}})

    def step(self) -> dict:
        return self._post("/step")

    def choose(self, index: int, chooser: dict) -> dict:
        """Answer the pending choice. chooser is {kind: player|agent, id?, note?}; RUE records it."""
        return self._post("/choose", {"indexes": [index], "chooser": chooser})

    def assert_fact(self, text: str) -> None:
        self._post("/assert", {"text": text})

    def query(self, text: str) -> dict:
        return self._post("/query", {"text": text})

    def explain(self, name: str, args: list[str]) -> dict:
        return self._post("/explain", {"name": name, "args": args})

    def facts(self) -> list[dict]:
        response = self.http.get("/facts")
        response.raise_for_status()
        return response.json()["facts"]


def pick(policy: str, agent: str, candidates: list[dict], rng: random.Random) -> tuple[int, dict]:
    """Return (candidate index, chooser) for one decision. This is where an LLM will go."""
    choosable = [c for c in candidates if not c["belowFloor"]]
    if policy == "rue":
        index = next(c["index"] for c in choosable if c["isDefault"])
        return index, {"kind": "agent", "id": agent, "note": "took RUE's top-ranked move"}
    if policy == "random":
        return rng.choice(choosable)["index"], {"kind": "agent", "id": agent, "note": "picked at random"}
    while True:
        answer = input("  your pick: ").strip()
        if answer.isdigit() and any(c["index"] == int(answer) for c in choosable):
            note = input("  why? (optional): ").strip()
            return int(answer), {"kind": "player", **({"note": note} if note else {})}
        print("  not a valid index")


def run_tick(rue: RueClient, policy: str, rng: random.Random) -> int:
    """Step one tick, answering every pending choice. Returns the finished tick number."""
    result = rue.step()
    while result["status"] == "awaiting-choice":
        request = result["request"]
        agent = request["binding"]["SELF"]
        ranked = sorted(request["candidates"], key=lambda c: c["score"] or 0, reverse=True)
        print(f"  {agent}'s turn:")
        for c in ranked:
            marker = "*" if c["isDefault"] else " "
            print(f"   {marker} [{c['index']}] {c['label']:<32} utility {c['score']}")
        index, chooser = pick(policy, agent, request["candidates"], rng)
        chosen = next(c for c in request["candidates"] if c["index"] == index)
        print(f"    -> {chosen['label']}")
        result = rue.choose(index, chooser)
    return result["tick"]


def print_state(rue: RueClient) -> None:
    values = {(f["name"], tuple(f["args"])): f["value"] for f in rue.facts() if f["value"] is not None}
    print("  " + "  ".join(
        f"{a}: energy {values.get(('energy', (a,)), 5)}, wood {values.get(('wood', (a,)), 0)}"
        for a in AGENTS
    ))


def print_proof(node: dict, depth: int = 0) -> None:
    detail = f" ({node['detail']})" if node.get("detail") else ""
    tick = f" @tick {node['tick']}" if node.get("tick") is not None else ""
    print(f"  {'  ' * depth}{node['statement']}  [{node['via']}{detail}{tick}]")
    for child in node.get("support", []):
        print_proof(child, depth + 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--policy", choices=["rue", "random", "ask"], default="rue")
    parser.add_argument("--ticks", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--server", default="http://localhost:5174")
    args = parser.parse_args()

    rng = random.Random(args.seed)
    rue = RueClient(args.server, SCENARIO)

    rue.reset()
    rue.start(controlled_agents=AGENTS)
    print("Start:")
    print_state(rue)

    for i in range(args.ticks):
        if i == 1:
            # Stand-in for the game mirroring a state change into RUE.
            print("\nPython pushes a state change into RUE: energy(carol) = 1")
            rue.assert_fact("energy(carol) = 1")
        print(f"\nTick {i + 1}:")
        tick = run_tick(rue, args.policy, rng)
        print(f"  tick {tick} complete")
        print_state(rue)

    tired = rue.query("energy.low(?X)")
    print(f"\nQuery energy.low(?X): {[row['X'] for row in tired['rows']]}")

    print("\nWhy does warmth(bob, alice) have its value?")
    print_proof(rue.explain("warmth", ["bob", "alice"])["proof"])


if __name__ == "__main__":
    main()
