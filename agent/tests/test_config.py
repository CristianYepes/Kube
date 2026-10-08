import copy
import json
import re
import subprocess
from pathlib import Path

from kube_agent import config, jev_client
from kube_agent.controller import TACTICS
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


def test_the_tactic_question_offers_the_controllers_tactics_in_the_planned_order():
    # Jev leans toward the first option of a Choice (TypeSafe's failure list), and ENGAGE goes first.
    assert config.questions() == {"tactic": config.TACTIC_QUESTION}
    assert config.TACTIC_QUESTION["type"] == "choice"
    assert list(config.TACTIC_QUESTION["criteria"]) == list(TACTICS) == ["ENGAGE", "KITE", "RETREAT", "SEARCH"]


def test_every_option_says_what_it_is_when_to_use_it_and_what_it_is_not_for():
    for name, entry in config.TACTIC_QUESTION["criteria"].items():
        assert set(entry) == {"what", "when", "not_for"}, name
        assert all(isinstance(text, str) and text.strip() for text in entry.values()), name


def test_the_question_is_part_of_the_config_hash_and_so_is_the_order_of_its_options(monkeypatch):
    first = config.config_sha256()

    reworded = copy.deepcopy(config.TACTIC_QUESTION)
    reworded["instructions"] += " (reworded)"
    monkeypatch.setattr(config, "TACTIC_QUESTION", reworded)
    assert config.config_sha256() != first

    reordered = copy.deepcopy(config.TACTIC_QUESTION)
    reordered["instructions"] = config.TACTIC_QUESTION["instructions"].removesuffix(" (reworded)")
    reordered["criteria"] = dict(reversed(list(reordered["criteria"].items())))
    monkeypatch.setattr(config, "TACTIC_QUESTION", reordered)
    assert config.config_sha256() != first  # the same options in another order are another config


def test_the_confidence_threshold_starts_at_a_third_and_is_part_of_the_config_hash(monkeypatch):
    # The owner's decision of 2026-10-06 on R12: 0.6 would have applied none of 50 real answers.
    assert config.CONFIDENCE_THRESHOLD == 0.3
    first = config.config_sha256()

    monkeypatch.setattr(config, "CONFIDENCE_THRESHOLD", 0.4)

    assert config.config_sha256() != first


def test_a_run_may_spend_five_cents_by_default():
    assert config.DEFAULT_RUN_BUDGET_USD == 0.05


# --- the freeze (T8) ----------------------------------------------------------------------------

FROZEN = REPO_ROOT / "agent" / "frozen.json"


def test_the_config_is_frozen_and_nothing_that_it_covers_has_changed_since():
    # frozen.json is written once, with the owner's OK, before the test seeds are touched. If this fails,
    # the question, theta or the cadence was edited after the freeze: that is a new config, and it needs
    # a new freeze (and the owner's OK), not a change to this file.
    frozen = json.loads(FROZEN.read_text())

    assert frozen["config_sha256"] == config.config_sha256()
    assert (frozen["decision_interval"], frozen["confidence_threshold"]) == (config.DECISION_INTERVAL, config.CONFIDENCE_THRESHOLD)
    assert frozen["model"] == jev_client.MODEL


def test_the_freeze_says_when_it_was_made_and_on_what_it_was_tuned():
    frozen = json.loads(FROZEN.read_text())

    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", frozen["frozen_on"])
    assert all(seed <= 20 for seed in frozen["tuned_on_seeds"])  # development seeds only
    assert re.fullmatch(r"[0-9a-f]{64}", frozen["config_sha256"])
