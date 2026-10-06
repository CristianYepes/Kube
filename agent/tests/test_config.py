from pathlib import Path

from kube_agent.config import DEFAULT_MAP, REPO_ROOT as CONFIG_REPO_ROOT

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repo_root_is_the_folder_with_the_game_sources():
    # Computed twice on purpose: a wrong number of parents in config.py would fail here.
    assert CONFIG_REPO_ROOT == REPO_ROOT
    assert (CONFIG_REPO_ROOT / "sources" / "jev" / "agent_main.c").is_file()


def test_default_map_exists_in_the_repository():
    # The path is relative to the repo root, where the game runs (docker and local runners).
    assert (REPO_ROOT / DEFAULT_MAP).is_file()
