"""The strip of spec 003 (agent/strip.py), which `kube-agent run --strip` puts over the game window. It runs with the
system Python of the owner's Linux (Ubuntu 22.04: Python 3.10, with GTK), not with uv's Python, so it is loaded as a file."""

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

from kube_agent.controller import TACTICS

SCRIPT = Path(__file__).resolve().parents[1] / "strip.py"


@pytest.fixture
def strip():
    spec = importlib.util.spec_from_file_location("strip", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_it_parses_as_python_3_10_the_system_python_of_ubuntu_22_04():
    ast.parse(SCRIPT.read_text(), feature_version=(3, 10))


def test_it_knows_the_four_tactics_of_the_agent_and_says_what_each_one_does(strip):
    assert strip.TACTICS == TACTICS
    assert set(strip.WHAT) == set(TACTICS)


@pytest.mark.parametrize("line, keys", [
    ("C 0 0 0 0 0 0 0", set()),
    ("C 1 0 0 0 0 0 0", {"W"}),
    ("C 0 1 0 0 0 0 0", {"S"}),
    ("C 0 0 1 0 0 0 0", {"A"}),
    ("C 0 0 0 1 0 0 0", {"D"}),
    ("C 0 0 0 0 1 0 0", {"←"}),
    ("C 0 0 0 0 0 1 0", {"→"}),
    ("C 0 0 0 0 0 0 1", {"↑"}),
    ("C 1 0 1 0 0 1 1", {"W", "A", "→", "↑"}),
])
def test_a_command_line_lights_the_keys_the_game_reads_from_it(strip, line, keys):
    assert strip.held_keys(line) == keys


@pytest.mark.parametrize("line", ["Q", "", "C 1 0 0", "C 1 0 0 0 0 0 2", "X 0 0 0 0 0 0 0", "C 1 0 0 0 0 0 0 1"])
def test_anything_else_is_not_a_command_line(strip, line):
    with pytest.raises(ValueError):
        strip.held_keys(line)


def test_the_tail_reads_only_complete_lines_and_each_one_once(strip, tmp_path):
    path = tmp_path / "keys.jsonl"
    tail = strip.Tail(path)
    assert tail.read() == ([], [])  # the file is not there yet

    path.write_text('{"t": 0.1, "keys": "C 1 0 0 0 0 0 0"}\n{"t": 0.2, "ke')
    assert tail.read() == ([{"t": 0.1, "keys": "C 1 0 0 0 0 0 0"}], [])

    with path.open("a") as file:
        file.write('ys": "C 0 0 0 0 0 0 0"}\nnot json\n')
    rows, problems = tail.read()
    assert rows == [{"t": 0.2, "keys": "C 0 0 0 0 0 0 0"}]
    assert len(problems) == 1 and problems[0].startswith("keys.jsonl line 3:")
    assert tail.read() == ([], [])


def test_it_says_who_is_playing(strip):
    assert strip.Strip("jev").who == "JEV IS PLAYING"
    assert strip.Strip("scripted").who == "THE RULE BOT IS PLAYING"


def test_before_the_first_decision_it_says_the_game_is_starting(strip):
    assert strip.Strip("jev").line() == ("", "the game is starting")


def test_it_shows_the_tactic_in_force_and_not_a_decision_that_was_not_applied(strip):
    shown = strip.Strip("jev")

    assert shown.take([{"tactic": "KITE", "applied": True}], [], None) is True
    assert shown.line() == ("KITE", strip.WHAT["KITE"])
    assert shown.take([{"tactic": "SEARCH", "applied": False, "reason": "stale"}], [], None) is False
    assert shown.line()[0] == "KITE"


def test_the_keys_are_those_of_the_last_line_sent_and_a_bad_row_is_reported(strip):
    shown = strip.Strip("scripted")

    shown.take([], [{"t": 0.1, "keys": "C 1 0 0 0 0 0 0"}, {"t": 0.2, "keys": "C 0 0 1 0 0 0 1"}, {"t": 0.3}], None)

    assert shown.keys == {"A", "↑"}
    assert len(shown.problems) == 1


@pytest.mark.parametrize("result, ending", [
    ({"outcome": "win", "survival_seconds": 11.12}, "WON in 11.1 s"),
    ({"outcome": "lose", "survival_seconds": 7.25}, "LOST at 7.2 s"),
    ({"outcome": "timeout", "survival_seconds": 180.0}, "TIME UP at 180.0 s"),
    ({"outcome": "error", "error": "BridgeError: the game is gone"}, "STOPPED"),
])
def test_at_the_end_it_says_how_the_game_ended_and_lets_go_of_the_keys(strip, result, ending):
    shown = strip.Strip("jev")
    shown.take([{"tactic": "ENGAGE", "applied": True}], [{"t": 9.0, "keys": "C 1 0 0 0 0 0 1"}], None)

    assert shown.take([], [], result) is True
    assert shown.line() == (ending, "") and shown.keys == frozenset() and shown.ended


def test_the_strip_sits_a_margin_in_from_the_bottom_left_of_the_work_area(strip):
    assert strip.bottom_left(area_x=0, area_y=27, area_height=773, strip_height=90, margin=24) == (24, 686)


def run_script(*args):
    return subprocess.run([sys.executable, "-I", str(SCRIPT), *args], capture_output=True, text=True, timeout=30)


def test_it_needs_a_run_folder_and_a_policy():
    done = run_script()

    assert done.returncode == 2 and "usage" in done.stderr


@pytest.mark.skipif(importlib.util.find_spec("gi") is not None, reason="GTK for Python is installed here: the script would open a window")
def test_without_gtk_it_says_how_to_install_it_and_fails(tmp_path):
    done = run_script(str(tmp_path), "scripted")

    assert done.returncode == 1
    assert "sudo apt install python3-gi gir1.2-gtk-3.0" in done.stderr
