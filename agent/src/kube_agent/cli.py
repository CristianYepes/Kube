"""Command line of the agent: `kube-agent run | eval | spend | latency | order-check`."""

import argparse
import sys

from kube_agent.config import DEFAULT_MAP

# The tasks that implement each subcommand are in specs/002-jev-agent/tasks.md.
SUBCOMMANDS_WITH_MAP = ["run", "eval"]
SUBCOMMANDS_WITHOUT_MAP = ["spend", "latency", "order-check"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="kube-agent",
        description="Jev picks the tactic in the cub3D zombie mode; code aims, fires and moves.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    for name in SUBCOMMANDS_WITH_MAP:
        subparser = subparsers.add_parser(name)
        subparser.add_argument("--map", default=DEFAULT_MAP, help="map file, relative to the repo root")
    for name in SUBCOMMANDS_WITHOUT_MAP:
        subparsers.add_parser(name)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"kube-agent {args.command}: not implemented yet", file=sys.stderr)
    return 1
