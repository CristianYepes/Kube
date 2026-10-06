"""Constants shared by the agent. Paths are relative to the repository root, where the game runs."""

import hashlib
import json
from pathlib import Path

# agent/src/kube_agent/config.py -> three folders up is the repository root. This holds for the
# editable install that `uv sync` makes; a copied wheel would not know where the game is.
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNS_DIR = REPO_ROOT / "agent" / "runs"  # committed, never ignored (FR15)

DEFAULT_MAP = "maps/bonus/subject_map.cub"
DEFAULT_MAX_SECONDS = 180.0  # of game time per episode
TOTAL_BUDGET_USD = 1.00  # for every Jev call of the whole spec (spec.md, Decision 3)

DECISION_INTERVAL = 0.5  # seconds of game time between decisions; one of the three things T8 may tune


def config_sha256() -> str:
    """A hash of what tuning may change, written into every result.json.

    Today that is only the decision cadence. T8 adds the question's text and the confidence
    threshold, and freezes the hash with the date in agent/frozen.json.
    """
    tunable = {"decision_interval": DECISION_INTERVAL}
    return hashlib.sha256(json.dumps(tunable, sort_keys=True).encode()).hexdigest()
