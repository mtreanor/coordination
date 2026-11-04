"""Play one Run: some work, some social layer, one Situation.

The RUE social layer needs the RUE server (from the repo root):

    cd external/rue && npm run server

Then:

    uv run scripts/play.py                                   # stub work, RUE social layer, random choosers
    uv run scripts/play.py --social off                      # the work-only condition
    uv run scripts/play.py --chooser claude-haiku --situation grudge
    uv run scripts/play.py --principals alice=claude-haiku,bob=qwen-9b --chooser gemini-flash-lite
    uv run scripts/play.py --rue-judgement                   # RUE's ranking picks the judgement actions
    uv run scripts/play.py --plan no-judgement               # social actions, but nothing is judged

The social round is one tick of the RUE scenario's tick plan (--plan), so conditions
are tick plans in rue-data/<scenario>/tickplans/.

Works are listed in coordination.work.WORKS and social layers in
coordination.social.SOCIAL_LAYERS. Output goes to runs/<time>-<work>-<social>-<situation>/.
"""

import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from coordination.agents import make_chooser
from coordination.run import Run
from coordination.situation import Situation
from coordination.social import SOCIAL_LAYERS, NoSocial, RueSocial
from coordination.work import WORKS

AGENTS = ["alice", "bob", "carol", "dave"]


def show(agent, phase, request, decision):
    if decision.passed:
        print(f"  [{phase}] {agent} passes ({(decision.error or 'no reason').splitlines()[0][:80]})")
        return
    label = next(o.label for o in request.options if o.id == decision.choice_id)
    print(f"  [{phase}] {agent}: {label}")
    if decision.rationale and decision.chooser_kind == "agent" and decision.model:
        print(f'      "{decision.rationale}"')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", default="stub", choices=sorted(WORKS))
    parser.add_argument("--social", default="rue", choices=sorted(SOCIAL_LAYERS))
    parser.add_argument("--scenario", default="stub-social", help="the RUE scenario for --social rue")
    parser.add_argument("--situation", default="neutral", help="a file in situations/, without .toml")
    parser.add_argument("--chooser", default="random", help="rue, random, ask, or a profile name from models.toml")
    parser.add_argument("--principals", default="", help="per-agent choosers, e.g. alice=claude-haiku,bob=qwen-9b")
    parser.add_argument("--rounds", type=int, default=4)
    parser.add_argument("--plan", default="full", help="the RUE tick plan for the social round (e.g. full, no-judgement)")
    parser.add_argument("--rue-judgement", action="store_true", help="RUE's ranking picks judgement actions instead of the agents")
    parser.add_argument("--hide-scores", action="store_true", help="don't show RUE's utilities to the agents")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--server", default="http://localhost:5174")
    args = parser.parse_args()

    load_dotenv()
    situation = Situation.load(args.situation)
    work = WORKS[args.work](AGENTS, rounds=args.rounds)
    social = (NoSocial() if args.social == "off" else
              RueSocial(args.scenario, args.server, plan=args.plan, rue_judgement=args.rue_judgement))

    assigned = dict(pair.split("=", 1) for pair in args.principals.split(",") if pair)
    unknown = set(assigned) - set(work.agents)
    if unknown:
        raise SystemExit(f"No agent named {sorted(unknown)} (agents: {work.agents})")
    names = {agent: assigned.get(agent, args.chooser) for agent in work.agents}
    choosers = {agent: make_chooser(name, args.seed + i) for i, (agent, name) in enumerate(names.items())}

    social_label = args.social if args.social == "off" else f"{args.social}-{args.plan}"
    run_dir = Path("runs") / f"{datetime.now():%Y%m%d-%H%M%S}-{args.work}-{social_label}-{args.situation}"
    print(f"Work: {args.work}  Social: {args.social}  Situation: {args.situation}")
    print("Principals: " + ", ".join(f"{agent} -> {name}" for agent, name in names.items()))

    run = Run(work, social, choosers, situation, run_dir, show_scores=not args.hide_scores, on_decision=show)
    original_ask = run.ask

    def ask(agent, phase, prompt, options):
        if phase == "work" and agent == work.agents[0]:
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
