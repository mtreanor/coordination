"""Proof of concept: agents choose campfire actions in RUE, driven entirely from Python.

Start the RUE server first (from the repo root):

    cd external/rue && npm run server

or start it with the authoring tool mounted, to watch the run in the Play tab:

    cd external/rue/tools/action-rule-set-tool && npm run dev

Then pick who chooses:

    uv run poc/rue_api_poc.py                       # RUE's top-ranked move, no LLM
    uv run poc/rue_api_poc.py --chooser random      # random (seeded)
    uv run poc/rue_api_poc.py --chooser ask         # you pick at the prompt
    uv run poc/rue_api_poc.py --chooser qwen-9b     # any profile in models.toml

Or give each principal its own chooser (the rest use --chooser):

    uv run poc/rue_api_poc.py --principals alice=claude-haiku,bob=gemini-flash-lite,carol=qwen-9b,dave=gemma-12b

Every decision is "controlled": RUE scores the candidates and pauses, and the
chooser picks, telling RUE who chose and why (recorded on the ActionRecord).
The script also pushes a fact into RUE mid-run (the way the game will mirror
state changes) and asks RUE to explain a fact at the end. Every decision is
logged to runs/<time>-poc-<chooser>/decisions.jsonl.
"""

import argparse
from datetime import datetime
from pathlib import Path
from statistics import mean

from dotenv import load_dotenv

from coordination.agents import (
    Chooser, DecisionLog, DecisionRequest, HumanChooser, LLMChooser, Option,
    RandomChooser, TopRankedChooser, load_profiles,
)
from coordination.rue_client import RueClient

SCENARIO = "poc"
INSTRUCTIONS = "Keep the camp going through the night: keep yourself rested, gather wood, and look after the others."


def make_chooser(name: str, seed: int) -> Chooser:
    if name == "rue":
        return TopRankedChooser()
    if name == "random":
        return RandomChooser(seed)
    if name == "ask":
        return HumanChooser()
    profiles = load_profiles()
    if name not in profiles:
        raise SystemExit(f"Unknown chooser {name!r}: use rue, random, ask, or one of {sorted(profiles)}")
    return LLMChooser(profiles[name])


def campfire_briefing(rue: RueClient, agent: str) -> str:
    """What the agent sees: the world's facts, rendered by RUE through each predicate's
    "briefing" template. No language model is involved."""
    lines = [f"It is night at the campfire. You are {agent}."]
    lines += [f"- {text}" for text in rue.render("briefing")]
    return "\n".join(lines)


def run_tick(rue: RueClient, choosers: dict[str, Chooser], log: DecisionLog, show_scores: bool, stats: list[dict]) -> int:
    """Step one tick, answering every pending choice with that agent's own chooser."""
    result = rue.step()
    while result["status"] == "awaiting-choice":
        pending = result["request"]
        agent = pending["binding"]["SELF"]
        chooser = choosers[agent]
        candidates = [c for c in pending["candidates"] if not c["belowFloor"]]
        request = DecisionRequest(
            agent=agent,
            instructions=INSTRUCTIONS,
            briefing=campfire_briefing(rue, agent),
            options=[Option(id=c["index"], label=c["label"], score=c["score"], is_default=c["isDefault"]) for c in candidates],
            show_scores=show_scores,
        )
        decision = chooser.choose(request)
        log.write(request, decision, tick=pending["tick"])

        default = next((o.id for o in request.options if o.is_default), None)
        stats.append({"agent": agent, "passed": decision.passed, "agreed": decision.choice_id == default,
                      "latency": decision.latency_s, "cost": (decision.usage or {}).get("cost")})
        if decision.passed:
            print(f"  {agent} passes ({(decision.error or 'no reason given').splitlines()[0][:80]})")
        else:
            label = next(o.label for o in request.options if o.id == decision.choice_id)
            marker = "" if decision.choice_id == default else "  [against RUE's ranking]"
            print(f"  {label}{marker}   ({decision.model or chooser.__class__.__name__})")
            if decision.rationale:
                print(f'      "{decision.rationale}"')

        result = rue.choose([] if decision.passed else [decision.choice_id], decision.rue_chooser())
    return result["tick"]


def print_proof(node: dict, depth: int = 0) -> None:
    detail = f" ({node['detail']})" if node.get("detail") else ""
    tick = f" @tick {node['tick']}" if node.get("tick") is not None else ""
    print(f"  {'  ' * depth}{node['statement']}  [{node['via']}{detail}{tick}]")
    for child in node.get("support", []):
        print_proof(child, depth + 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--chooser", default="rue", help="rue, random, ask, or a profile name from models.toml")
    parser.add_argument("--principals", default="", help="per-agent choosers, e.g. alice=claude-haiku,bob=qwen-9b")
    parser.add_argument("--ticks", type=int, default=3)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--hide-scores", action="store_true", help="don't show RUE's utilities to the chooser")
    parser.add_argument("--server", default="http://localhost:5174")
    args = parser.parse_args()

    load_dotenv()
    rue = RueClient(SCENARIO, args.server)
    rue.reset()
    rue.start(controlled_agents=[])
    agents = rue.entities("agent")
    assigned = dict(pair.split("=", 1) for pair in args.principals.split(",") if pair)
    unknown = set(assigned) - set(agents)
    if unknown:
        raise SystemExit(f"No agent named {sorted(unknown)} in the scenario (agents: {agents})")
    names = {agent: assigned.get(agent, args.chooser) for agent in agents}
    choosers = {agent: make_chooser(name, args.seed) for agent, name in names.items()}
    label = "mixed" if len(set(names.values())) > 1 else args.chooser
    run_dir = Path("runs") / f"{datetime.now():%Y%m%d-%H%M%S}-poc-{label}"
    log = DecisionLog(run_dir / "decisions.jsonl")

    print("Principals: " + ", ".join(f"{agent} -> {name}" for agent, name in names.items()))
    rue.start(controlled_agents=agents)
    stats: list[dict] = []
    for i in range(args.ticks):
        if i == 1:
            # Stand-in for the game mirroring a state change into RUE.
            print("\nPython pushes a state change into RUE: energy(carol) = 1")
            rue.assert_fact("energy(carol) = 1")
        print(f"\nTick {i + 1}:")
        run_tick(rue, choosers, log, not args.hide_scores, stats)

    print()
    for agent, name in names.items():
        mine = [s for s in stats if s["agent"] == agent]
        latencies = [s["latency"] for s in mine if s["latency"] is not None]
        cost = sum(s["cost"] or 0 for s in mine)
        print(f"{agent} ({name}): {len(mine)} decisions, {sum(s['agreed'] for s in mine)} agreed with RUE, "
              f"{sum(s['passed'] for s in mine)} passed"
              + (f", {mean(latencies):.1f}s each" if latencies else "")
              + (f", ${cost:.4f}" if cost else ""))

    print("\nWhy does warmth(bob, alice) have its value?")
    print_proof(rue.explain("warmth", ["bob", "alice"])["proof"])
    print(f"\nLog: {log.path}")


if __name__ == "__main__":
    main()
