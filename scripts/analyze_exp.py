"""Summarise an experiment batch (scripts/batch.py output) per condition: scores, who did
what to whom in the work, what was said, and how it was taken. Works for Not My Bug and the
Investment Club.

    uv run scripts/analyze_exp.py runs/batch-exp1-testimony-<time>
    uv run scripts/analyze_exp.py runs/<batch> --pairs alice:bob carol:bob --after 3
    uv run scripts/analyze_exp.py runs/<batch> --quotes bob --phase work

Per condition (mean over its Runs; the Run is the unit):

- team total and each agent's score;
- work moves between pairs named by --pairs (actor:target), counted over every round and
  over rounds after --after: Not My Bug passes and help, Club investments;
- the social actions chosen, by kind (claims, accounts, confrontations, ...), and how
  listeners judged them (believed, took in, doubted, no real opinion);
- with --quotes NAME, the rationales of decisions in --phase whose chosen option names NAME.
"""

import argparse
import json
import re
import statistics
from collections import Counter, defaultdict
from pathlib import Path


def load(path: Path, name: str):
    p = path / name
    if not p.exists():
        import gzip
        p = path / (name + ".gz")
        return [json.loads(l) for l in gzip.open(p, "rt")] if p.exists() else []
    return [json.loads(l) for l in p.open()]


def chosen(record):
    cid = (record.get("decision") or {}).get("choice_id")
    for option in record["request"]["options"]:
        if option.get("id") == cid:
            return option["label"]
    return None


def moves(rounds):
    """(round, actor, kind, target) for every work move between two agents."""
    out = []
    for r in rounds:
        work = r["work"]
        if "moves" in work:  # Not My Bug
            for actor, m in work["moves"].items():
                if m["move"] in ("pass", "help") and m["target"]:
                    out.append((r["round"], actor, m["move"], m["target"]))
        for inv in work.get("investments") or []:  # the Investment Club
            out.append((r["round"], inv["investor"], "invest", inv["recipient"]))
    return out


SOCIAL_KINDS = [
    (r"tells (\w+) what (\w+) did", "account"),
    (r"tells (\w+) that (\w+) is (\w+)", "claim:{3}"),
    (r"confronts", "confront"), (r"thanks", "thank"), (r"apologises", "apologise"),
    (r"cold shoulder", "cold shoulder"), (r"says nothing", "say nothing"),
]
JUDGE_KINDS = [
    (r"believes", "believe"), (r"takes in", "take in"), (r"doubts", "doubt"),
    (r"no real opinion", "no opinion"), (r"accepts", "accept"), (r"refuses", "refuse"),
    (r"to heart", "to heart"), (r"resents", "resent"),
]


def kind(label, table):
    for pattern, name in table:
        m = re.search(pattern, label)
        if m:
            return name.format(*([None] + list(m.groups()))) if "{" in name else name
    return "other"


def summarise(run: Path, pairs, after):
    rounds = load(run, "rounds.jsonl")
    decisions = load(run, "decisions.jsonl")
    if not rounds:
        return None
    scores = rounds[-1]["scores"]
    out = {"team": sum(scores.values()), "scores": scores, "pairs": {}, "pairs_after": {},
           "social": Counter(), "judge": Counter(), "labels": Counter(),
           "final_social": rounds[-1].get("social", {})}
    for pair in pairs:
        a, t = pair.split(":")
        for rnd, actor, k, target in moves(rounds):
            if actor == a and target == t:
                out["pairs"][f"{a}->{t} {k}"] = out["pairs"].get(f"{a}->{t} {k}", 0) + 1
                if rnd > after:
                    out["pairs_after"][f"{a}->{t} {k}"] = out["pairs_after"].get(f"{a}->{t} {k}", 0) + 1
    shares = defaultdict(list)  # Club: share of grown coins a recipient sent back to an investor
    for r in rounds:
        for p in r["work"].get("paybacks") or []:
            if p["grown"]:
                shares[f"{p['recipient']}->{p['investor']} payback share"].append((r["round"], p["sent_back"] / p["grown"]))
    for pair in pairs:
        key = pair.replace(":", "->") + " payback share"
        if shares.get(key):
            out["pairs"][key] = mean([v for _, v in shares[key]])
            late = [v for rnd, v in shares[key] if rnd > after]
            if late:
                out["pairs_after"][key] = mean(late)
    for d in decisions:
        label = chosen(d) or ""
        if d["phase"] == "social actions":
            out["social"][kind(label, SOCIAL_KINDS)] += 1
        elif d["phase"] == "social judgement":
            out["judge"][kind(label, JUDGE_KINDS)] += 1
        elif d["phase"] == "work judgement":
            m = re.search(r"calls it (\w+) of (\w+)", label)
            out["labels"][f"{m[1]}:{m[2]}" if m else ("bad luck" if "bad luck" in label else "no opinion")] += 1
    return out


def mean(xs):
    return statistics.mean(xs) if xs else 0.0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("batch", type=Path)
    ap.add_argument("--pairs", nargs="*", default=[])
    ap.add_argument("--after", type=int, default=0)
    ap.add_argument("--quotes", default=None)
    ap.add_argument("--phase", default="work")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    by_condition = defaultdict(list)
    for run in sorted(p for p in args.batch.iterdir() if p.is_dir()):
        cond = re.sub(r"-seed\d+$", "", run.name)
        s = summarise(run, args.pairs, args.after)
        if s:
            by_condition[cond].append((run.name, s))

    agents = sorted({a for runs in by_condition.values() for _, s in runs for a in s["scores"]})
    print("| condition | Runs | team | " + " | ".join(agents) + " |")
    print("|---|---|---|" + "---|" * len(agents))
    for cond, runs in by_condition.items():
        teams = [s["team"] for _, s in runs]
        per = [f"{mean([s['scores'][a] for _, s in runs]):.1f}" for a in agents]
        print(f"| {cond} | {len(runs)} | {mean(teams):.1f} ({', '.join(f'{t:g}' for t in teams)}) | " + " | ".join(per) + " |")

    if args.pairs:
        keys = sorted({k for runs in by_condition.values() for _, s in runs for k in s["pairs"]})
        print(f"\nWork moves between pairs, mean per Run (all rounds / after round {args.after}):\n")
        print("| condition | " + " | ".join(keys) + " |")
        print("|---|" + "---|" * len(keys))
        for cond, runs in by_condition.items():
            cells = [f"{mean([s['pairs'].get(k, 0) for _, s in runs]):.1f} / {mean([s['pairs_after'].get(k, 0) for _, s in runs]):.1f}" for k in keys]
            print(f"| {cond} | " + " | ".join(cells) + " |")

    for title, field in (("Social actions chosen", "social"), ("Social judgements", "judge"), ("Work judgement labels (label:named)", "labels")):
        keys = sorted({k for runs in by_condition.values() for _, s in runs for k in s[field]})
        if not keys:
            continue
        print(f"\n{title}, mean per Run:\n")
        print("| condition | " + " | ".join(keys) + " |")
        print("|---|" + "---|" * len(keys))
        for cond, runs in by_condition.items():
            print(f"| {cond} | " + " | ".join(f"{mean([s[field].get(k, 0) for _, s in runs]):.1f}" for k in keys) + " |")

    print("\nFinal social state (first Run of each condition):")
    for cond, runs in by_condition.items():
        name, s = runs[0]
        if any(s["final_social"].values()):
            print(f"\n{name}:")
            for agent, text in s["final_social"].items():
                print(f"  {agent}: " + text.replace("\n", " | "))

    if args.quotes:
        print(f"\nRationales ({args.phase}) whose choice names {args.quotes}:")
        for cond, runs in by_condition.items():
            for name, _ in runs:
                for d in load(args.batch / name, "decisions.jsonl"):
                    label = chosen(d) or ""
                    if d["phase"] == args.phase and re.search(rf"\b{args.quotes}\b", label) and d["request"]["agent"] != args.quotes:
                        why = (d.get("decision") or {}).get("rationale") or ""
                        print(f"- [{name} r{d['round']}] {d['request']['agent']}: {label} — {why[:240]}")

    if args.json:
        args.json.write_text(json.dumps({c: [s for _, s in runs] for c, runs in by_condition.items()}, indent=1, default=dict))


if __name__ == "__main__":
    main()
