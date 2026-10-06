from pathlib import Path

from kube_agent.config import DEFAULT_MAP

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_default_map_exists_in_the_repository():
    # The path is relative to the repo root, where the game runs (docker and local runners).
    assert (REPO_ROOT / DEFAULT_MAP).is_file()
