"""The demo strip of spec 003 (agent/strip_demo.py). It runs with the system Python of the owner's Linux (Ubuntu 22.04:
Python 3.10, with GTK), not with uv's Python, so these tests read it as a file."""

import ast
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "strip_demo.py"


def load():
    spec = importlib.util.spec_from_file_location("strip_demo", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_it_parses_as_python_3_10_the_system_python_of_ubuntu_22_04():
    ast.parse(SCRIPT.read_text(), feature_version=(3, 10))


def test_the_strip_sits_a_margin_in_from_the_bottom_left_of_the_work_area():
    assert load().bottom_left(area_x=0, area_y=27, area_height=773, strip_height=60, margin=24) == (24, 716)


@pytest.mark.skipif(importlib.util.find_spec("gi") is not None, reason="GTK for Python is installed here: the script would open a window")
def test_without_gtk_it_says_how_to_install_it_and_fails():
    done = subprocess.run([sys.executable, "-I", str(SCRIPT)], capture_output=True, text=True, timeout=30)

    assert done.returncode == 1
    assert "sudo apt install python3-gi gir1.2-gtk-3.0" in done.stderr
