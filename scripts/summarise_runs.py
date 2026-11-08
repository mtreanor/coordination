"""Summarise Not My Bug Run directories: what each agent did each sprint, who received the
passes, what the social layer's choices were, and (optionally) the agents' own rationales.

    uv run scripts/summarise_runs.py findings/runs/neutral-defector-social findings/runs/neutral-defector-workonly
    uv run scripts/summarise_runs.py findings/runs/neutral-defector-social --target bob --after 3
    uv run scripts/summarise_runs.py findings/runs/neutral-defector-workonly --rationales 2-4

Reads a Run directory as play.py writes it (config.json, rounds.jsonl, events.jsonl,
decisions.jsonl) or as findings/ keeps it (decisions.jsonl.gz).
"""

import argparse
import gzip
import json
import re
from collections import Counter
from pathlib import Path


def decisions(run: Path) -> list[dict]:
    plain, packed = run / "decisions.jsonl", run / "decisions.jsonl.gz"
    text = plain.read_text() if plain.exists() else gzip.open(packed, "rt").read()
    return [json.loads(line) for line in text.splitlines()]


def chosen(decision: dict) -> dict | None:
    options = {o["id"]: o for o in decision["request"]["options"]}
    return options.get(decision["decision"]["choice_id"])


def kind(label: str, agents: list[str]) -> str:
    """A social option's label without the actor and the names: the kind of action."""
    rest = label.split(" ", 1)[1] if " " in label else label
    return re.sub(r"\b(" + "|".join(map(re.escape, agents)) + r")\b", "X", rest)


def summarise(run: Path, target: str | None, after: int, rationales: tuple[int, int] | None) -> None:
    config = json.loads((run / "config.json").read_text())
    rounds = [json.loads(line) for line in (run / "rounds.jsonl").read_text().splitlines()]
    ds = decisions(run)
    agents = config["agents"]
    print(f"\n=== {run.name}")
    print(f"social: {config['social']['layer']}  situations: {config.get('situations', config.get('situation'))}  "
          f"choosers: {sorted(set(config['choosers'].values()))}  seed: {config['seed']}  commit: {config.get('commit')}")
    instructions = {d["request"]["agent"]: d["request"]["instructions"] for d in ds}
    for agent in agents:
        if instructions.get(agent):
            print(f"instructions for {agent}: {instructions[agent]!r}")
    final = rounds[-1]["scores"]
    print(f"final hours: {final}  team: {sum(final.values())}")
    received, late = Counter(), Counter()
    print("moves by sprint:")
    for r in rounds:
        moves = r["work"]["moves"]
        print(f"  {r['round']:>2}: " + ", ".join(
            f"{a}={m['move']}" + (f">{m['target']}" if m.get("target") else "") for a, m in moves.items()))
        for m in moves.values():
            if m["move"] == "pass":
                received[m["target"]] += 1
                if r["round"] > after:
                    late[m["target"]] += 1
    print(f"passes received: {dict(received)} (of {sum(received.values())})")
    if target:
        print(f"passes to {target} after sprint {after}: {late[target]} of {sum(late.values())}")
    social = Counter()
    for d in ds:
        if d["phase"] != "work" and (pick := chosen(d)):
            social[(d["phase"], kind(pick["label"], agents))] += 1
    phases = sorted({p for p, _ in social})
    for phase in phases:
        print(f"[{phase}] " + "; ".join(f"{n} {k}" for (p, k), n in social.most_common() if p == phase))
    if rationales:
        lo, hi = rationales
        print("work rationales:")
        for d in ds:
            if d["phase"] == "work" and lo <= d["round"] <= hi:
                pick = chosen(d)
                print(f"  {d['round']} {d['request']['agent']} [{pick['label'] if pick else '?'}] {d['decision']['rationale']}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("runs", nargs="+", type=Path)
    parser.add_argument("--target", help="count the passes to this agent")
    parser.add_argument("--after", type=int, default=0, help="with --target: only sprints after this one")
    parser.add_argument("--rationales", help="print work rationales for these sprints, e.g. 2-4")
    args = parser.parse_args()
    span = None
    if args.rationales:
        lo, _, hi = args.rationales.partition("-")
        span = (int(lo), int(hi or lo))
    for run in args.runs:
        summarise(run, args.target, args.after, span)


if __name__ == "__main__":
    main()
