"""Command line of the agent: `kube-agent run | eval | spend | latency | order-check`."""

import argparse
import asyncio
import sys

from kube_agent.bridge import BridgeError
from kube_agent.config import DEFAULT_MAP, DEFAULT_MAX_SECONDS
from kube_agent.episode import run_episode, summarize
from kube_agent.policies import POLICIES

# The tasks that implement each stub are in specs/002-jev-agent/tasks.md.
STUBS_WITH_MAP = ["eval"]
STUBS_WITHOUT_MAP = ["spend", "latency", "order-check"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kube-agent",
        description="Jev picks the tactic in the cub3D zombie mode; code aims, fires and moves.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="play one episode and keep its logs under agent/runs/")
    run.add_argument("--policy", required=True, choices=POLICIES)
    run.add_argument("--seed", required=True, type=int)
    run.add_argument("--map", default=DEFAULT_MAP, help="map file, relative to the repo root")
    run.add_argument("--runner", choices=["docker", "local"], default="docker",
                     help="docker: the game in the kube-dev container; local: on this machine")
    run.add_argument("--max-seconds", type=float, default=DEFAULT_MAX_SECONDS, help="of game time")

    for name in STUBS_WITH_MAP:
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--map", default=DEFAULT_MAP, help="map file, relative to the repo root")
    for name in STUBS_WITHOUT_MAP:
        subparsers.add_parser(name)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        return _run(args)
    print(f"kube-agent {args.command}: not implemented yet", file=sys.stderr)
    return 1


def _run(args: argparse.Namespace) -> int:
    try:
        result = asyncio.run(run_episode(args.policy, args.seed, args.map, args.runner, args.max_seconds))
    except (BridgeError, OSError) as error:  # OSError: a missing map, or a run folder that already exists
        print(f"kube-agent run: {error}", file=sys.stderr)
        return 1
    print(summarize(result))
    return 0
