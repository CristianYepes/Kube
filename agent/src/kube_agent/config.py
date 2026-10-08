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
LATENCY_PROBE_BUDGET_USD = 0.01  # three times the estimate for 50 calls (about $0.003), as a safety stop
ORDER_CHECK_BUDGET_USD = 0.02  # twice the estimate for 100 states asked three times (300 calls, about $0.0094)
DEFAULT_RUN_BUDGET_USD = 0.05  # what one `kube-agent run --policy jev` may spend (plan.md, "Budget ledger")

DECISION_INTERVAL = 0.5  # seconds of game time between decisions; one of the three things T8 may tune
CONFIDENCE_THRESHOLD = 0.3  # apply Jev's answer when its confidence is at least this; T8 may tune it (R12)

# The question Jev answers (specs/002-jev-agent/plan.md, "The question"). The descriptions say what the
# controller really does with each tactic, because Jev reads them literally. The ORDER of the options
# is part of the question: jev-1.13 leans toward the first one of a Choice, so T8 checks it.
TACTIC_QUESTION = {
    "type": "choice",
    "instructions": (
        "Pick the tactic for the next half second of a zombie-survival shooter. Read `threats`, `player` and "
        "`space` in the state. The code aims and fires by itself; you only pick what the body does."
    ),
    "criteria": {
        "ENGAGE": {
            "what": "Stand and shoot the nearest threat.",
            "when": "a threat is in view and not touching, and health is not low",
            "not_for": "several threats close at once",
        },
        "KITE": {
            "what": "Step straight back from the nearest threat while facing and shooting it.",
            "when": "threats are close and there is open space behind",
            "not_for": "being cornered",
        },
        "RETREAT": {
            "what": (
                "Move along a path to the open area farthest from every threat, still facing and shooting "
                "the nearest one."
            ),
            "when": "health is low, or you are being hit by more than one threat",
            "not_for": "a single wounded threat you can finish",
        },
        "SEARCH": {
            "what": "Move toward the remaining threats that are out of view.",
            "when": "no threat is in view but some remain",
            "not_for": "any threat in view",
        },
    },
}


def questions() -> dict:
    """The questions of one request, by id. Built on each call so the hash always sees the current text."""
    return {"tactic": TACTIC_QUESTION}


def config_sha256() -> str:
    """A hash of what tuning may change, written into every result.json.

    That is the decision cadence, the confidence threshold and the question. T8 freezes the hash
    with the date in agent/frozen.json. The keys are NOT sorted: the order of the
    options is part of the question, so the same options in another order are another config.
    """
    tunable = {
        "decision_interval": DECISION_INTERVAL,
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "questions": questions(),
    }
    return hashlib.sha256(json.dumps(tunable).encode()).hexdigest()
