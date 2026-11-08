"""Play one Run, described by a Run config in configs/ (ADR 0005).

The RUE social layer needs the RUE server (from the repo root):

    cd external/rue && npm run server

Then:

    uv run scripts/play.py configs/investment-club.toml          # a Run config
    uv run scripts/play.py configs/investment-club.toml --social off --rounds 2
    uv run scripts/play.py                                       # stub work, RUE social layer, random choosers
    uv run scripts/play.py configs/stub.toml --chooser claude-haiku --situations office-history,bob-defects
    uv run scripts/play.py configs/stub.toml --choosers alice=claude-haiku,bob=qwen-9b

Flags override the config file. The social round is one tick of the RUE scenario's tick
plan (plan), so conditions are tick plans in rue-data/<scenario>/tickplans/.

Works are listed in coordination.work.WORKS. Output goes to
runs/<time>-<work>-<social>-<situations>/, with the resolved settings in config.json.
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from coordination.config import RunConfig
from coordination.run import Run


def show(agent, phase, request, decision):
    if decision.passed:
        print(f"  [{phase}] {agent} passes ({(decision.error or 'no reason').splitlines()[0][:80]})")
        return
    label = next(o.label for o in request.options if o.id == decision.choice_id)
    print(f"  [{phase}] {agent}: {label}")
    if decision.rationale and decision.chooser_kind == "agent" and decision.model:
        print(f'      "{decision.rationale}"')


def apply_flags(config: RunConfig, args: argparse.Namespace) -> RunConfig:
    top = {k: getattr(args, k) for k in ("work", "rounds", "seed") if getattr(args, k) is not None}
    social = {k: v for k, v in {"layer": args.social, "scenario": args.scenario, "plan": args.plan,
                                "server": args.server}.items() if v is not None}
    choosers = dict(config.choosers)
    if args.chooser:
        choosers["default"] = args.chooser
    choosers.update(dict(pair.split("=", 1) for pair in (args.choosers or "").split(",") if pair))
    if args.situations is not None:
        top["situations"] = [s for s in args.situations.split(",") if s]
    if args.agents:
        top["agents"] = args.agents.split(",")
    return config.model_copy(update={**top, "choosers": choosers,
                                     "social": config.social.model_copy(update=social)})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("config", nargs="?", help="a Run config (TOML), e.g. configs/investment-club.toml")
    parser.add_argument("--work")
    parser.add_argument("--agents", help="comma-separated agent names")
    parser.add_argument("--social", help="rue or off")
    parser.add_argument("--scenario", help="the RUE scenario for --social rue")
    parser.add_argument("--situations", help="files in situations/, without .toml, comma-separated, combined in order; \"\" for the neutral start")
    parser.add_argument("--chooser", help="the default chooser: rue, random, ask, or a profile from models.toml")
    parser.add_argument("--choosers", help="per-agent choosers, e.g. alice=claude-haiku,bob=qwen-9b")
    parser.add_argument("--rounds", type=int, help="override the work's length, for short test Runs")
    parser.add_argument("--plan", help="the RUE tick plan for the social round (e.g. full)")
    parser.add_argument("--seed", type=int)
    parser.add_argument("--server")
    parser.add_argument("--out", help="the Run's output directory (default: runs/<time>-<label>)")
    parser.add_argument("--quiet", action="store_true", help="don't print each decision")
    args = parser.parse_args()

    load_dotenv()
    config = apply_flags(RunConfig.load(args.config) if args.config else RunConfig(), args)
    work = config.make_work()
    situation = config.load_situation(work.agents)
    config.check_cast(work.agents)
    social = config.make_social()
    choosers = config.make_choosers(work.agents)

    run_dir = Path(args.out) if args.out else Path("runs") / f"{datetime.now():%Y%m%d-%H%M%S}-{config.label()}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "config.json").write_text(json.dumps(config.manifest(work.agents), indent=2) + "\n")
    print(f"Run: {config.name}  Work: {config.work}  Social: {config.social.layer}  Situations: {config.situation_label()}")
    print("Choosers: " + ", ".join(f"{agent} -> {name}" for agent, name in config.chooser_names(work.agents).items()))

    run = Run(work, social, choosers, situation, run_dir, on_decision=None if args.quiet else show)
    original_ask = run.ask
    last_round = [0]

    def ask(agent, phase, prompt, options):
        if run.round != last_round[0]:
            last_round[0] = run.round
            if not args.quiet:
                print(f"\nRound {run.round}")
        return original_ask(agent, phase, prompt, options)

    run.ask = ask
    scores = run.play()

    print("\nScores: " + ", ".join(f"{agent} {score:g}" for agent, score in scores.items())
          + f"  (total {sum(scores.values()):g})")
    for agent in work.agents:
        beliefs = social.briefing(agent)
        if beliefs:
            print(f"\n{agent} believes:\n{beliefs}")
    print(f"\nRun output: {run_dir}")


if __name__ == "__main__":
    main()
