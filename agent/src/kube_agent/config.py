"""Constants shared by the agent. Paths are relative to the repository root, where the game runs."""

from pathlib import Path

# agent/src/kube_agent/config.py -> three folders up is the repository root. This holds for the
# editable install that `uv sync` makes; a copied wheel would not know where the game is.
REPO_ROOT = Path(__file__).resolve().parents[3]

DEFAULT_MAP = "maps/bonus/subject_map.cub"
