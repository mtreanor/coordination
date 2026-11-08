"""Play a batch of paired Runs: the same Run config under several conditions, once per seed,
so each seed gives one Run per condition that differs only in the condition (the work's own
randomness, the agents and each agent's model seed are the same across a pair).

An experiment file names the conditions (experiments/*.toml):

    uv run scripts/batch.py experiments/history-neutral-defector.toml
    uv run scripts/batch.py experiments/history-neutral-defector.toml --runs 1    # a batch of 1

    description = "..."
    config = "configs/not-my-bug-rue-smoke.toml"   # the base Run config
    runs = 10                                     # seeds (pairs) per condition
    rounds = 10                                   # optional, like chooser, parallel, first_seed
    chooser = "gemini-flash"

    [conditions.history]                          # the first condition is the baseline
    situations = ["office-history"]
    [conditions.neutral]
    situations = []
    [conditions.work-only]
    social = "off"

A condition overrides the base config with any of: social (rue or off), situations, plan,
chooser, choosers (per agent, a table). Command-line flags override the experiment file.

Or, without an experiment file, each condition is a value for play.py's --social:

    uv run scripts/batch.py configs/not-my-bug-rue-smoke.toml --social rue off \\
        --chooser gemini-flash --rounds 10 --runs 10 --parallel 4

Runs go in parallel; every worker that needs RUE gets its own RUE server (a server holds one play session per
scenario, so two Runs can't share one), started here on its own port and stopped at the end.

Output goes to runs/batch-<time>/: one directory per Run (<condition>-seed<N>), and
summary.md / summary.json: per condition, the mean and spread of the team's total score,
the lowest agent's score and the work events by kind; and per pair, the difference in the
team's total between the first condition and each other, with a bootstrap 95% interval
over seeds. The unit is the Run: agents in one Run aren't independent.
"""

import argparse
import json
import os
import queue
import random
import statistics
import subprocess
import sys
import time
import tomllib
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
RUE = ROOT / "external" / "rue"
BASE_PORT = 5190


def start_servers(count: int) -> list[tuple[subprocess.Popen, str]]:
    servers = []
    for i in range(count):
        port = BASE_PORT + i
        proc = subprocess.Popen(["node", "src/server/main.js"], cwd=RUE, env={**os.environ, "PORT": str(port)},
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        servers.append((proc, f"http://localhost:{port}"))
    for _, url in servers:
        for _ in range(60):
            try:
                httpx.get(f"{url}/api/play/_/session", timeout=1)
                break
            except httpx.HTTPError:
                time.sleep(0.5)
        else:
            raise SystemExit(f"RUE server at {url} didn't start")
    return servers


CONDITION_KEYS = {"social", "situations", "plan", "chooser", "choosers"}


def flags(settings: dict) -> list[str]:
    """play.py flags for a condition's settings."""
    cmd = []
    for key, value in settings.items():
        if value is None:
            continue
        if key == "situations":
            value = ",".join(value)
        elif key == "choosers":
            value = ",".join(f"{agent}={name}" for agent, name in value.items())
        cmd += [f"--{key}", str(value)]
    return cmd


def play(args, condition: str, settings: dict, seed: int, out: Path, server: str | None) -> dict:
    cmd = [sys.executable, "scripts/play.py", args.config, "--seed", str(seed), "--out", str(out), "--quiet"]
    cmd += flags({"chooser": args.chooser, "rounds": args.rounds, "situations": args.situations,
                  "choosers": args.choosers, **settings})
    if server:
        cmd += ["--server", server]
    log = out.with_suffix(".log")
    out.parent.mkdir(parents=True, exist_ok=True)
    with log.open("w") as f:
        code = subprocess.run(cmd, cwd=ROOT, stdout=f, stderr=subprocess.STDOUT).returncode
    return {"condition": condition, "seed": seed, "dir": str(out), "ok": code == 0, **(measure(out) if code == 0 else {})}


def measure(run_dir: Path) -> dict:
    rounds = [json.loads(line) for line in (run_dir / "rounds.jsonl").read_text().splitlines()]
    events = [e for line in (run_dir / "events.jsonl").read_text().splitlines() for e in json.loads(line)["events"]]
    scores = rounds[-1]["scores"]
    targeted = Counter(e["target"] for e in events if e.get("target"))
    return {
        "scores": scores,
        "team": sum(scores.values()),
        "lowest": min(scores.values()),
        "events": dict(Counter(e["kind"] for e in events)),
        "most_targeted_share": round(max(targeted.values()) / sum(targeted.values()), 2) if targeted else 0.0,
    }


def bootstrap(diffs: list[float], reps: int = 10000, seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(reps))
    return means[int(0.025 * reps)], means[int(0.975 * reps) - 1]


def summarise(results: list[dict], conditions: list[str]) -> tuple[dict, str]:
    ok = [r for r in results if r["ok"]]
    summary = {"conditions": {}, "pairs": {}, "failed": [r["dir"] for r in results if not r["ok"]]}
    lines = ["# Batch summary", "", "| condition | Runs | team total (mean ± sd) | lowest agent (mean) | most-targeted share (mean) | events per Run (mean) |",
             "|---|---|---|---|---|---|"]
    for c in conditions:
        rs = [r for r in ok if r["condition"] == c]
        if not rs:
            continue
        team = [r["team"] for r in rs]
        kinds = sorted({k for r in rs for k in r["events"]})
        events = {k: round(statistics.fmean(r["events"].get(k, 0) for r in rs), 1) for k in kinds}
        sd = statistics.stdev(team) if len(team) > 1 else 0.0
        summary["conditions"][c] = {"runs": len(rs), "team_mean": statistics.fmean(team), "team_sd": sd,
                                    "lowest_mean": statistics.fmean(r["lowest"] for r in rs),
                                    "most_targeted_share_mean": statistics.fmean(r["most_targeted_share"] for r in rs),
                                    "events_mean": events}
        lines.append(f"| {c} | {len(rs)} | {statistics.fmean(team):.1f} ± {sd:.1f} | "
                     f"{summary['conditions'][c]['lowest_mean']:.1f} | "
                     f"{summary['conditions'][c]['most_targeted_share_mean']:.2f} | "
                     + ", ".join(f"{k}: {v}" for k, v in events.items()) + " |")
    base = conditions[0]
    by_seed = {(r["condition"], r["seed"]): r for r in ok}
    for c in conditions[1:]:
        seeds = sorted(s for (cond, s) in by_seed if cond == c and (base, s) in by_seed)
        diffs = [by_seed[(c, s)]["team"] - by_seed[(base, s)]["team"] for s in seeds]
        if not diffs:
            continue
        lo, hi = bootstrap(diffs) if len(diffs) > 1 else (diffs[0], diffs[0])
        summary["pairs"][f"{c} - {base}"] = {"pairs": len(diffs), "mean_diff": statistics.fmean(diffs),
                                             "ci95": [lo, hi], "diffs": diffs,
                                             "higher": sum(d > 0 for d in diffs), "lower": sum(d < 0 for d in diffs)}
        lines += ["", f"**{c} − {base}**, team total, {len(diffs)} pairs: mean {statistics.fmean(diffs):+.1f}, "
                      f"bootstrap 95% interval [{lo:+.1f}, {hi:+.1f}]; {c} higher in "
                      f"{sum(d > 0 for d in diffs)}, lower in {sum(d < 0 for d in diffs)}."]
    if summary["failed"]:
        lines += ["", "Failed Runs (see their .log): " + ", ".join(summary["failed"])]
    return summary, "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("file", help="an experiment file (experiments/*.toml) or a Run config (configs/*.toml)")
    parser.add_argument("--social", nargs="+", help="without an experiment file: the conditions (default: rue off); the first is the baseline for differences")
    parser.add_argument("--runs", type=int, help="seeds (pairs) per condition (default 10)")
    parser.add_argument("--first-seed", type=int)
    parser.add_argument("--parallel", type=int)
    parser.add_argument("--chooser")
    parser.add_argument("--rounds", type=int)
    parser.add_argument("--situations", help="comma-separated, for every condition")
    parser.add_argument("--out", help="the batch directory (default: runs/batch-<experiment or time>)")
    args = parser.parse_args()
    args.choosers = None

    data = tomllib.loads(Path(args.file).read_text())
    experiment = "conditions" in data
    if experiment:
        if args.social:
            raise SystemExit("--social is for a Run config; an experiment file names its own conditions")
        conditions = data["conditions"]
        for name, settings in conditions.items():
            unknown = set(settings) - CONDITION_KEYS
            if unknown:
                raise SystemExit(f"Condition {name!r} has unknown settings {sorted(unknown)} (known: {sorted(CONDITION_KEYS)})")
        args.config = data["config"]
        for key in ("runs", "first_seed", "parallel", "chooser", "rounds"):
            if getattr(args, key) is None and key in data:
                setattr(args, key, data[key])
        if args.situations is None and "situations" in data:
            args.situations = data["situations"]
        args.choosers = data.get("choosers")
    else:
        args.config = args.file
        conditions = {c: {"social": c} for c in (args.social or ["rue", "off"])}
    if isinstance(args.situations, str):
        args.situations = [s for s in args.situations.split(",") if s]
    args.runs = 10 if args.runs is None else args.runs
    args.first_seed = args.first_seed or 0
    args.parallel = args.parallel or 4

    base_layer = tomllib.loads(Path(args.config).read_text()).get("social", {}).get("layer", "rue")
    uses_rue = {name: settings.get("social", base_layer) != "off" for name, settings in conditions.items()}

    stamp = f"{datetime.now():%Y%m%d-%H%M%S}"
    default_out = f"batch-{Path(args.file).stem}-{stamp}" if experiment else f"batch-{stamp}"
    batch = Path(args.out) if args.out else ROOT / "runs" / default_out
    batch.mkdir(parents=True, exist_ok=True)
    jobs = [(c, s) for s in range(args.first_seed, args.first_seed + args.runs) for c in conditions]
    (batch / "batch.json").write_text(json.dumps({**vars(args), "conditions": conditions,
                                                  "experiment": data if experiment else None,
                                                  "started": datetime.now().isoformat()}, indent=2) + "\n")

    needs_rue = any(uses_rue.values())
    servers = start_servers(min(args.parallel, len(jobs))) if needs_rue else []
    free: queue.Queue = queue.Queue()
    for _, url in servers:
        free.put(url)

    def job(condition: str, seed: int) -> dict:
        server = free.get() if uses_rue[condition] else None
        try:
            return play(args, condition, conditions[condition], seed, batch / f"{condition}-seed{seed}", server)
        finally:
            if server:
                free.put(server)

    results = []
    try:
        with ThreadPoolExecutor(max_workers=args.parallel) as pool:
            futures = [pool.submit(job, c, s) for c, s in jobs]
            for done, future in enumerate(as_completed(futures), 1):
                r = future.result()
                results.append(r)
                status = f"team {r['team']:g}" if r["ok"] else "FAILED"
                print(f"[{done}/{len(jobs)}] {r['condition']} seed {r['seed']}: {status}", flush=True)
    finally:
        for proc, _ in servers:
            proc.terminate()

    summary, text = summarise(results, list(conditions))
    (batch / "summary.json").write_text(json.dumps({"results": results, **summary}, indent=2) + "\n")
    (batch / "summary.md").write_text(text)
    print("\n" + text + f"\nBatch output: {batch}")


if __name__ == "__main__":
    main()
