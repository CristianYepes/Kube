import re
import subprocess
from pathlib import Path

from kube_agent import config
from kube_agent.config import DEFAULT_MAP, REPO_ROOT as CONFIG_REPO_ROOT

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_repo_root_is_the_folder_with_the_game_sources():
    # Computed twice on purpose: a wrong number of parents in config.py would fail here.
    assert CONFIG_REPO_ROOT == REPO_ROOT
    assert (CONFIG_REPO_ROOT / "sources" / "jev" / "agent_main.c").is_file()


def test_default_map_exists_in_the_repository():
    # The path is relative to the repo root, where the game runs (docker and local runners).
    assert (REPO_ROOT / DEFAULT_MAP).is_file()


def test_runs_are_kept_in_agent_runs_and_git_does_not_ignore_them():
    # FR15: every run is committed. If a .gitignore rule ever swallowed them, the logs and the
    # spend ledger would vanish without a sound. `git check-ignore -q` exits 1 for "not ignored".
    assert config.RUNS_DIR == REPO_ROOT / "agent" / "runs"

    check = subprocess.run(["git", "check-ignore", "-q", "agent/runs/x/result.json"], cwd=REPO_ROOT)

    assert check.returncode == 1


def test_config_sha256_is_a_stable_hash_of_what_can_be_tuned(monkeypatch):
    first = config.config_sha256()

    assert re.fullmatch(r"[0-9a-f]{64}", first)
    assert config.config_sha256() == first
    monkeypatch.setattr(config, "DECISION_INTERVAL", 0.6)
    assert config.config_sha256() != first
