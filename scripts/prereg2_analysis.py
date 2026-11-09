"""The preregistered analysis of the second study (docs/experiments/prereg2-paragraph-vs-rue.md, section 6).

    uv run scripts/prereg2_analysis.py runs/batch-prereg2-club-haiku [--json out.json]

A 2x2 on claude-haiku-5-5: the standing introduction (neutral or social-life) crossed with RUE
(off or on). It reuses the first study's measures and tests (scripts/prereg_analysis.py), adds
the honest agents' payback share in round 1, and runs the registered contrasts. Nothing here
is chosen after seeing the data: a change after registration is a deviation (section 9).
"""

import argparse
import json
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from prereg_analysis import DEFECTOR, boot_ci, holm, lines, load_batch, model_of, sign_flip  # noqa: E402

MATCHED, PARAGRAPH, RUE_ONLY, SOCIAL = "work-only-matched", "paragraph-only", "rue-only", "social"

# (name, outcome, how the per-seed difference is formed, sides, family)
TESTS = [
    ("RUE adds to the paragraph", "team_coins", (SOCIAL, PARAGRAPH), 2, "primary"),
    ("the paragraph alone", "team_coins", (PARAGRAPH, MATCHED), 2, "secondary"),
    ("RUE alone", "team_coins", (RUE_ONLY, MATCHED), 2, "secondary"),
    ("interaction", "team_coins", "interaction", 2, "secondary"),
    ("RUE adds to the paragraph: paying back", "others_payback_share", (SOCIAL, PARAGRAPH), 2, "secondary"),
    ("RUE adds to the paragraph: investing", "investments", (SOCIAL, PARAGRAPH), 2, "secondary"),
    ("study 1's H1 again", "team_coins", (SOCIAL, MATCHED), 1, "secondary"),
]


def round1_payback(run: Path) -> float | None:
    """The honest agents' payback share in round 1, before any social round has happened."""
    ps = [p for p in lines(run / "rounds.jsonl")[0]["work"]["paybacks"] if p["recipient"] != DEFECTOR and p["grown"]]
    return sum(p["sent_back"] for p in ps) / sum(p["grown"] for p in ps) if ps else None


def diffs(runs: dict, outcome: str, how) -> list[float]:
    """Per-seed differences, skipping seeds where a value is missing (no paybacks to measure)."""
    seeds = sorted({s for _, s in runs})
    out = []
    for s in seeds:
        if how == "interaction":
            cells = [runs.get((c, s), {}).get(outcome) for c in (SOCIAL, PARAGRAPH, RUE_ONLY, MATCHED)]
            if None not in cells:
                out.append((cells[0] - cells[1]) - (cells[2] - cells[3]))
        else:
            a, b = (runs.get((c, s), {}).get(outcome) for c in how)
            if a is not None and b is not None:
                out.append(a - b)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("batch", type=Path)
    ap.add_argument("--json", type=Path)
    args = ap.parse_args()

    runs, excluded = load_batch(args.batch)
    for (c, s), m in runs.items():
        m["round1_payback_share"] = round1_payback(args.batch / f"{c}-seed{s}")
    print(f"Investment Club 2x2, {model_of(args.batch)}: {len(runs)} Runs in {args.batch}")
    if excluded:
        print("Excluded:", "; ".join(f"{n}: {why}" for n, why in excluded))

    keys = list(next(iter(runs.values())))
    print("\nPer condition (mean over Runs with a value):")
    for c in (MATCHED, PARAGRAPH, RUE_ONLY, SOCIAL):
        vals = {k: [m[k] for (c2, _), m in runs.items() if c2 == c and m[k] is not None] for k in keys}
        print(f"  {c} (n={sum(1 for c2, _ in runs if c2 == c)}): "
              + ", ".join(f"{k}={statistics.fmean(v):.2f}" for k, v in vals.items() if v))

    base = [m for (c, _), m in runs.items() if c == MATCHED]
    d = [m["defector_payback_share"] for m in base if m["defector_payback_share"] is not None]
    o = [m["others_payback_share"] for m in base if m["others_payback_share"] is not None]
    ok = bool(d and o) and statistics.fmean(d) < statistics.fmean(o)
    print(f"\nManipulation check (in {MATCHED}): bob's payback share {statistics.fmean(d) if d else float('nan'):.2f} "
          f"vs others' {statistics.fmean(o) if o else float('nan'):.2f}: {'PASSED' if ok else 'FAILED'}")

    print("\nRegistered tests (paired by seed; exact sign-flip test; 95% bootstrap CI of the mean difference):")
    rows = []
    for name, outcome, how, sides, family in TESTS:
        ds = diffs(runs, outcome, how)
        if not ds:
            continue
        contrast = "(social - paragraph-only) - (rue-only - matched)" if how == "interaction" else f"{how[0]} - {how[1]}"
        rows.append({"test": name, "outcome": outcome, "contrast": contrast, "sides": sides, "family": family,
                     "pairs": len(ds), "mean_diff": statistics.fmean(ds), "ci95": boot_ci(ds),
                     "positive": sum(x > 0 for x in ds), "negative": sum(x < 0 for x in ds),
                     "p": sign_flip(ds, sides), "diffs": ds})
    secondary = [r for r in rows if r["family"] == "secondary"]
    for r, p in zip(secondary, holm([r["p"] for r in secondary])):
        r["p_holm"] = p
    for r in rows:
        lo, hi = r["ci95"]
        p = f"p={r['p']:.4f}" + (f", Holm p={r['p_holm']:.4f}" if "p_holm" in r else "")
        print(f"  [{r['family']}] {r['test']}: {r['outcome']}, {r['contrast']} "
              f"({'one' if r['sides'] == 1 else 'two'}-sided): mean diff {r['mean_diff']:+.3f} [{lo:+.3f}, {hi:+.3f}], "
              f"{r['positive']}+/{r['negative']}- of {r['pairs']}, {p}")

    print("\nDescriptive (registered): the honest agents' round-1 payback share, by condition:")
    for c in (MATCHED, PARAGRAPH, RUE_ONLY, SOCIAL):
        v = [m["round1_payback_share"] for (c2, _), m in runs.items() if c2 == c and m["round1_payback_share"] is not None]
        print(f"  {c}: {statistics.fmean(v):.2f} over {len(v)} Runs with a round-1 payback" if v else f"  {c}: none")

    if args.json:
        args.json.write_text(json.dumps({"batch": str(args.batch), "model": model_of(args.batch),
                                         "excluded": excluded, "manipulation_check_passed": ok,
                                         "runs": {f"{c}-seed{s}": m for (c, s), m in sorted(runs.items())},
                                         "tests": rows}, indent=2) + "\n")


if __name__ == "__main__":
    main()
