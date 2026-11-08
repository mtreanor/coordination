"""The preregistered analysis (docs/experiments/prereg-confirmatory.md, section 6).

    uv run scripts/prereg_analysis.py runs/batch-prereg-club-<time>                     # one model
    uv run scripts/prereg_analysis.py runs/batch-prereg-club-<time> runs/batch-prereg-club-haiku-<time>
                                                                  # both models, and the comparison

Reads only the Run directories (<condition>-seed<N>/) and their logs. Prints every
registered measure per Run, the manipulation check, and the registered tests; --json
writes the same as JSON. Nothing here is chosen after seeing the data: a change to this
file after registration is a deviation (prereg section 9).

The unit is the Run. Conditions are paired by seed: a seed fixes the Club's dice, menu orders and each agent's model seed, so a pair differs only in the condition.
"""

import argparse
import gzip
import itertools
import json
import random
import statistics
from pathlib import Path

DEFECTOR = "bob"
BASELINE = "work-only-matched"
TREATMENT = "social"
UNMATCHED = "work-only"
BOOT = 10_000


def lines(path: Path) -> list[dict]:
    """A JSONL log, or its gzipped copy (prereg-runs/ keeps decision logs gzipped)."""
    if not path.exists() and path.with_name(path.name + ".gz").exists():
        text = gzip.decompress(path.with_name(path.name + ".gz").read_bytes()).decode()
    else:
        text = path.read_text()
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def passes_rate(run: Path) -> float:
    """Share of an agent's decisions with no valid choice (prereg section 7)."""
    decisions = lines(run / "decisions.jsonl")
    if not decisions:
        return 1.0
    return sum(1 for d in decisions if (d.get("decision") or {}).get("choice_id") is None) / len(decisions)


def club(run: Path) -> dict:
    rounds = lines(run / "rounds.jsonl")
    scores = rounds[-1]["scores"]
    investments = [(r["round"], i) for r in rounds for i in r["work"]["investments"]]
    paybacks = [p for r in rounds for p in r["work"]["paybacks"]]

    def share(who, among):
        ps = [p for p in paybacks if among(p["recipient"], who) and p["grown"]]
        return sum(p["sent_back"] for p in ps) / sum(p["grown"] for p in ps) if ps else None

    return {
        "team_coins": sum(scores.values()),                                       # H1 primary
        "investments": len(investments),                                          # H1 secondary
        "coins_invested": sum(i["amount"] for _, i in investments),               # exploratory
        "investments_in_defector_after_round_1": sum(1 for rnd, i in investments
                                                     if rnd > 1 and i["recipient"] == DEFECTOR),  # secondary
        "defector_coins": scores[DEFECTOR],                                       # secondary
        "defector_payback_share": share(DEFECTOR, lambda r, w: r == w),           # manipulation check
        "others_payback_share": share(DEFECTOR, lambda r, w: r != w),             # manipulation check
    }


# The registered tests: (outcome, contrast, sides, family). "primary" is the one confirmatory
# test (H1); the "secondary" tests are Holm-corrected together.
TESTS = [
    ("team_coins", (TREATMENT, BASELINE), 1, "primary"),
    ("investments", (TREATMENT, BASELINE), 1, "secondary"),
    ("investments_in_defector_after_round_1", (TREATMENT, BASELINE), 2, "secondary"),
    ("team_coins", (UNMATCHED, BASELINE), 2, "secondary"),
]


def sign_flip(diffs: list[float], sides: int) -> float:
    """Exact paired permutation test: every assignment of signs to the paired differences."""
    observed = statistics.fmean(diffs)
    count = total = 0
    for signs in itertools.product((1, -1), repeat=len(diffs)):
        stat = statistics.fmean(s * d for s, d in zip(signs, diffs))
        total += 1
        count += (abs(stat) >= abs(observed) - 1e-12) if sides == 2 else (stat >= observed - 1e-12)
    return count / total


def boot_ci(diffs: list[float], seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    means = sorted(statistics.fmean(rng.choices(diffs, k=len(diffs))) for _ in range(BOOT))
    return means[int(0.025 * BOOT)], means[int(0.975 * BOOT) - 1]


def holm(ps: list[float]) -> list[float]:
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adjusted, running = [0.0] * len(ps), 0.0
    for rank, i in enumerate(order):
        running = max(running, min(1.0, (len(ps) - rank) * ps[i]))
        adjusted[i] = running
    return adjusted


def load_batch(batch: Path) -> tuple[dict, list]:
    runs, excluded = {}, []
    for d in sorted(p for p in batch.iterdir() if p.is_dir() and "-seed" in p.name):
        condition, seed = d.name.rsplit("-seed", 1)
        if not (d / "rounds.jsonl").exists():
            excluded.append((d.name, "no rounds (Run failed)"))
            continue
        if (rate := passes_rate(d)) > 0.10:
            excluded.append((d.name, f"{rate:.0%} of decisions passed"))
            continue
        runs[(condition, int(seed))] = club(d)
    return runs, excluded


def model_of(batch: Path) -> str:
    """The models that made the batch's decisions, as their logs record them."""
    models = set()
    for d in batch.iterdir():
        if (d / "decisions.jsonl").exists() or (d / "decisions.jsonl.gz").exists():
            models |= {(r.get("decision") or {}).get("model") for r in lines(d / "decisions.jsonl")}
    return ", ".join(sorted(m for m in models if m)) or "?"


def paired(runs: dict, outcome: str, a: str, b: str) -> list[float]:
    seeds = sorted(s for (c, s) in runs if c == a and (b, s) in runs)
    return [runs[(a, s)][outcome] - runs[(b, s)][outcome] for s in seeds]


def analyse(batch: Path) -> dict:
    runs, excluded = load_batch(batch)
    conditions = sorted({c for c, _ in runs})
    out = {"work": "investment-club", "batch": str(batch), "model": model_of(batch),
           "excluded": excluded, "runs": {}, "tests": []}
    print(f"Investment Club, {out['model']}: {len(runs)} Runs in {batch}")
    for c, s in sorted(runs):
        out["runs"][f"{c}-seed{s}"] = runs[(c, s)]
    keys = list(next(iter(runs.values())))
    print("\nPer condition (mean; per-Run values in --json):")
    for c in conditions:
        vals = {k: [runs[(c2, s)][k] for (c2, s) in runs if c2 == c and runs[(c2, s)][k] is not None] for k in keys}
        print(f"  {c} (n={sum(1 for c2, _ in runs if c2 == c)}): "
              + ", ".join(f"{k}={statistics.fmean(v):.2f}" for k, v in vals.items() if v))
    if excluded:
        print("\nExcluded:", "; ".join(f"{n}: {why}" for n, why in excluded))

    print("\nManipulation check (in the baseline):")
    base = [m for (c, _), m in runs.items() if c == BASELINE]
    d = [m["defector_payback_share"] for m in base if m["defector_payback_share"] is not None]
    o = [m["others_payback_share"] for m in base if m["others_payback_share"] is not None]
    ok = bool(d and o) and statistics.fmean(d) < statistics.fmean(o)
    print(f"  bob's payback share {statistics.fmean(d) if d else float('nan'):.2f} vs others' "
          f"{statistics.fmean(o) if o else float('nan'):.2f}: {'PASSED' if ok else 'FAILED'}")
    out["manipulation_check_passed"] = ok

    print("\nRegistered tests (paired by seed; exact sign-flip test; 95% bootstrap CI of the mean paired difference):")
    rows = []
    for outcome, (a, b), sides, family in TESTS:
        diffs = paired(runs, outcome, a, b)
        if not diffs:
            continue
        rows.append({"outcome": outcome, "contrast": f"{a} - {b}", "sides": sides, "family": family,
                     "pairs": len(diffs), "mean_diff": statistics.fmean(diffs), "ci95": boot_ci(diffs),
                     "positive": sum(x > 0 for x in diffs), "negative": sum(x < 0 for x in diffs),
                     "p": sign_flip(diffs, sides)})
    secondary = [r for r in rows if r["family"] == "secondary"]
    for r, p in zip(secondary, holm([r["p"] for r in secondary])):
        r["p_holm"] = p
    for r in rows:
        lo, hi = r["ci95"]
        p = f"p={r['p']:.3f}" + (f", Holm p={r['p_holm']:.3f}" if "p_holm" in r else "")
        print(f"  [{r['family']}] {r['outcome']}, {r['contrast']} ({'one' if r['sides'] == 1 else 'two'}-sided): "
              f"mean diff {r['mean_diff']:+.2f} [{lo:+.2f}, {hi:+.2f}], {r['positive']}+/{r['negative']}- "
              f"of {r['pairs']} pairs, {p}")
    out["tests"] = rows
    out["primary_diffs"] = paired(runs, *PRIMARY)
    return out


PRIMARY = ("team_coins", TREATMENT, BASELINE)
PERMUTATIONS = 100_000


def label_permutation(x: list[float], y: list[float], seed: int = 0) -> float:
    """Two-sided permutation test of a difference in means between two independent sets
    (here, the two models' paired effects), by random relabelling."""
    rng = random.Random(seed)
    observed = abs(statistics.fmean(x) - statistics.fmean(y))
    pooled, n = x + y, len(x)
    hits = 0
    for _ in range(PERMUTATIONS):
        rng.shuffle(pooled)
        hits += abs(statistics.fmean(pooled[:n]) - statistics.fmean(pooled[n:])) >= observed - 1e-12
    return (hits + 1) / (PERMUTATIONS + 1)


def compare(first: dict, second: dict) -> dict:
    """H1 on both models (the two primary tests, Holm-corrected together), and the model
    comparison (a registered secondary test: do the models' effects differ?)."""
    prim = [next(r for r in o["tests"] if r["family"] == "primary") for o in (first, second)]
    adjusted = holm([r["p"] for r in prim])
    print("\nH1 on both models (one-sided; Holm across the two):")
    for o, r, p in zip((first, second), prim, adjusted):
        lo, hi = r["ci95"]
        print(f"  {o['model']}: mean diff {r['mean_diff']:+.2f} [{lo:+.2f}, {hi:+.2f}], "
              f"{r['positive']}+/{r['negative']}- of {r['pairs']} pairs, p={r['p']:.3f}, Holm p={p:.3f}"
              f" -> {'supported' if p < 0.05 else 'not supported'}"
              + ("" if o["manipulation_check_passed"] else " (manipulation check FAILED: uninterpretable)"))
    x, y = first["primary_diffs"], second["primary_diffs"]
    gap = statistics.fmean(x) - statistics.fmean(y)
    rng = random.Random(1)
    boots = sorted(statistics.fmean(rng.choices(x, k=len(x))) - statistics.fmean(rng.choices(y, k=len(y)))
                   for _ in range(BOOT))
    p = label_permutation(x, y)
    print(f"\nModel comparison (secondary, two-sided): {first['model']} effect minus {second['model']} effect "
          f"= {gap:+.2f} [{boots[int(0.025 * BOOT)]:+.2f}, {boots[int(0.975 * BOOT) - 1]:+.2f}], "
          f"permutation p={p:.3f} (underpowered: an estimate, not a test of small differences)")
    return {"h1": [{"model": o["model"], **r, "p_holm_models": q} for o, r, q in zip((first, second), prim, adjusted)],
            "model_difference": {"estimate": gap, "ci95": [boots[int(0.025 * BOOT)], boots[int(0.975 * BOOT) - 1]],
                                 "p": p}}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("batch", type=Path, help="the gemini-3.6-flash batch (or any one batch)")
    ap.add_argument("second", type=Path, nargs="?", help="the claude-haiku-5-5 batch, for H1 on both models")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()
    out = {"first": analyse(args.batch)}
    if args.second:
        print("\n" + "-" * 72 + "\n")
        out["second"] = analyse(args.second)
        out["comparison"] = compare(out["first"], out["second"])
    if args.json:
        args.json.write_text(json.dumps(out, indent=2) + "\n")


if __name__ == "__main__":
    main()
