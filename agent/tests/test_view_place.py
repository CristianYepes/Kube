"""Spec 003, V6: putting the game window where the page expects it, on X11, and telling the page where it landed.

`xdotool` and `xwininfo` are the owner's Linux tools. Most tests answer for them with `Tools` (the answers are the
format of the real programs, recorded in the container, tasks.md V6); one test runs real
subprocesses against two small scripts that stand in for them, so that the call itself (arguments, timeout, text mode) is run.
"""

import json
import subprocess
import threading
import time
from pathlib import Path

import pytest

from kube_agent import view

XWININFO = """
xwininfo: Window id: 0x400001 "cub3D"

  Absolute upper-left X:  {x}
  Absolute upper-left Y:  {y}
  Relative upper-left X:  {x}
  Relative upper-left Y:  {y}
  Width: {w}
  Height: {h}
  Depth: 24
  Visual: 0x21
  Visual Class: TrueColor
  Border width: 0
  Class: InputOutput
  Colormap: 0x20 (installed)
  Bit Gravity State: ForgetGravity
  Window Gravity State: NorthWestGravity
  Backing Store State: NotUseful
  Save Under State: no
  Map State: IsViewable
  Override Redirect State: no
  Corners:  +{x}+{y}  --{x}+{y}  --{x}--{y}  +{x}--{y}
  -geometry {w}x{h}+{x}+{y}
"""  # recorded from the real xwininfo (x11-utils) in the kube-dev container, 2026-10-11: the labels and their spacing are the program's


class Tools:
    """Stands in for subprocess.run: answers like xdotool and xwininfo, and remembers what it was asked."""

    def __init__(self, ids=("4194311",), offset=(0, 0), size=(1280, 720), missing=(), failing=(), hanging=(), info=None):
        self.ids, self.offset, self.size = ids, offset, size
        self.missing, self.failing, self.hanging, self.info = set(missing), set(failing), set(hanging), info
        self.calls, self.moved_to = [], (0, 0)

    def __call__(self, argv, **kwargs):
        self.calls.append((argv, kwargs))
        tool, verb = argv[0], argv[1]
        if tool in self.missing:
            raise FileNotFoundError(tool)
        if (tool, verb) in self.hanging:
            raise subprocess.TimeoutExpired(argv, kwargs["timeout"])
        if (tool, verb) in self.failing:
            return subprocess.CompletedProcess(argv, 1, "", "X Error of failed request: BadWindow")
        if (tool, verb) == ("xdotool", "search"):
            return subprocess.CompletedProcess(argv, 0, "".join(f"{i}\n" for i in self.ids), "")
        if (tool, verb) == ("xdotool", "windowmove"):
            self.moved_to = (int(argv[3]), int(argv[4]))
            return subprocess.CompletedProcess(argv, 0, "", "")
        if tool == "xwininfo":
            text = self.info if self.info is not None else XWININFO.format(
                x=self.moved_to[0] + self.offset[0], y=self.moved_to[1] + self.offset[1], w=self.size[0], h=self.size[1])
            return subprocess.CompletedProcess(argv, 0, text, "")
        raise AssertionError(f"unexpected call {argv}")


def place(tools, x=0, y=0):
    return view.place_game_window(x, y, run=tools, sleep=lambda seconds: None)


# --- the happy path ------------------------------------------------------------------------------------------------------


def test_the_window_is_found_by_its_name_moved_and_measured():
    tools = Tools(offset=(4, 37))

    layout, warnings = place(tools, 100, 50)

    assert layout == {"kind": "layout", "x": 104, "y": 87, "width": 1280, "height": 720} and warnings == []
    assert [call[0] for call in tools.calls] == [
        ["xdotool", "search", "--sync", "--name", "^cub3D$"],
        ["xdotool", "windowmove", "4194311", "100", "50"],
        ["xwininfo", "-id", "4194311"],
    ]


def test_the_layout_is_read_after_a_moment_for_the_window_manager_to_move_the_window():
    steps = []
    tools = Tools()
    original = tools.__call__

    def recording(argv, **kwargs):
        steps.append(argv[1] if argv[0] == "xdotool" else argv[0])
        return original(argv, **kwargs)

    view.place_game_window(0, 0, run=recording, sleep=lambda seconds: steps.append(("sleep", seconds)))

    assert steps == ["search", "windowmove", ("sleep", view.PLACE_SETTLE_SECONDS), "xwininfo"]


def test_every_call_to_a_tool_has_a_timeout():
    tools = Tools()
    place(tools)
    assert all(kwargs["timeout"] == view.PLACE_TIMEOUT_SECONDS and kwargs["capture_output"] and kwargs["text"] for _, kwargs in tools.calls)


def test_the_newest_window_is_the_one_that_is_moved_when_there_are_several():
    tools = Tools(ids=("4194311", "4194390"))
    place(tools)
    assert tools.calls[1][0][2] == "4194390"


def test_the_page_follows_where_the_window_really_is_and_not_where_it_was_asked():
    layout, warnings = place(Tools(offset=(4, 37)), 0, 0)
    assert (layout["x"], layout["y"]) == (4, 37) and warnings == []  # a title bar and a border are not a problem


# --- what goes wrong -----------------------------------------------------------------------------------------------------


@pytest.mark.parametrize("tool, hint", [("xdotool", "apt install xdotool"), ("xwininfo", "apt install x11-utils")])
def test_a_missing_tool_is_named_with_the_package_that_has_it(tool, hint):
    with pytest.raises(view.PlacementError) as error:
        place(Tools(missing=[tool]))
    assert tool in str(error.value) and hint in str(error.value)


def test_no_window_at_all_is_an_error_that_says_so():
    with pytest.raises(view.PlacementError, match="no window named cub3D"):
        place(Tools(ids=()))


@pytest.mark.parametrize("tool, verb", [("xdotool", "search"), ("xdotool", "windowmove"), ("xwininfo", "-id")])
def test_a_tool_that_does_not_finish_in_time_is_an_error_that_names_the_call(tool, verb):
    with pytest.raises(view.PlacementError, match=rf"{tool} {verb}.*did not finish in 10 s"):
        place(Tools(hanging=[(tool, verb)]))


@pytest.mark.parametrize("tool, verb", [("xdotool", "search"), ("xdotool", "windowmove"), ("xwininfo", "-id")])
def test_a_tool_that_fails_is_an_error_with_its_message(tool, verb):
    with pytest.raises(view.PlacementError, match=r"exit code 1.*BadWindow"):
        place(Tools(failing=[(tool, verb)]))


def test_an_answer_of_xwininfo_without_a_position_is_an_error():
    with pytest.raises(view.PlacementError, match="no 'Absolute upper-left X' line"):
        place(Tools(info="xwininfo: Window id: 0x1 \"cub3D\"\n  Width: 1280\n  Height: 720\n"))


def test_a_window_that_stays_far_from_the_corner_asked_for_is_reported():
    layout, warnings = place(Tools(offset=(640, 300)), 0, 0)  # a window the session would not let go
    assert (layout["x"], layout["y"]) == (640, 300)
    assert len(warnings) == 1 and "0,0" in warnings[0] and "Wayland" in warnings[0]


def test_a_window_of_another_size_is_reported():
    _, warnings = place(Tools(size=(1024, 768)))
    assert len(warnings) == 1 and "1024x768" in warnings[0] and "1280x720" in warnings[0]


def test_the_size_the_page_is_drawn_for_is_the_one_of_its_css():
    css = (view.PAGE_DIR / "index.html").read_text()
    assert f"left: {view.GAME_WIDTH}px" in css and f"top: {view.GAME_HEIGHT}px" in css


# --- the real call ---------------------------------------------------------------------------------------------------------


def test_the_calls_run_for_real_against_two_small_programs(tmp_path, monkeypatch):
    (tmp_path / "xdotool").write_text('#!/bin/sh\ncase "$1" in\n  search) echo 77 ;;\n  windowmove) echo "$3 $4" > "$0.moved" ;;\nesac\n')
    (tmp_path / "xwininfo").write_text('#!/bin/sh\nread x y < "$(dirname "$0")/xdotool.moved"\n'
                                       'echo "  Absolute upper-left X:  $x"\necho "  Absolute upper-left Y:  $y"\necho "  Width: 1280"\necho "  Height: 720"\n')
    for name in ("xdotool", "xwininfo"):
        (tmp_path / name).chmod(0o755)
    monkeypatch.setenv("PATH", f"{tmp_path}:/usr/bin:/bin")

    layout, warnings = view.place_game_window(12, 34, sleep=lambda seconds: None)

    assert layout == {"kind": "layout", "x": 12, "y": 34, "width": 1280, "height": 720} and warnings == []


# --- following with a placer --------------------------------------------------------------------------------------------------------


def run_follow(tmp_path, place, said):
    log, stop = view.EventLog(), threading.Event()
    thread = threading.Thread(target=view.follow, args=(log, stop),
                              kwargs={"runs_dir": tmp_path, "since": "20990101T000000Z", "say": said.append, "place": place}, daemon=True)
    thread.start()
    return log, stop, thread


def test_a_run_is_followed_by_the_layout_of_its_window(tmp_path):
    placed = []
    log, stop, thread = run_follow(tmp_path, lambda: placed.append(1) or ({"kind": "layout", "x": 4, "y": 37, "width": 1280, "height": 720}, []), [])
    (tmp_path / "20991231T000000Z-jev-s1-darwin").mkdir()
    time.sleep(0.3)
    stop.set()
    thread.join(1)

    assert [event["kind"] for event in log.after(-1)] == ["run", "layout"] and placed == [1]
    assert log.after(-1)[1]["x"] == 4


def test_each_run_gets_its_own_placement(tmp_path):
    placed = []
    log, stop, thread = run_follow(tmp_path, lambda: placed.append(1) or ({"kind": "layout", "x": 0, "y": 0, "width": 1280, "height": 720}, []), [])
    (tmp_path / "20991231T000000Z-jev-s1-darwin").mkdir()
    time.sleep(0.3)
    (tmp_path / "20991231T000100Z-jev-s2-darwin").mkdir()
    time.sleep(0.3)
    stop.set()
    thread.join(1)

    assert len(placed) == 2 and [event["kind"] for event in log.after(-1)] == ["run", "layout", "run", "layout"]


def test_a_placement_that_fails_is_said_and_the_run_goes_on(tmp_path):
    def fail():
        raise view.PlacementError("xdotool is not installed (sudo apt install xdotool)")

    said = []
    log, stop, thread = run_follow(tmp_path, fail, said)
    folder = tmp_path / "20991231T000000Z-jev-s1-darwin"
    folder.mkdir()
    time.sleep(0.2)
    (folder / "episode.jsonl").write_text(json.dumps({"t": 0.0, "tactic": "ENGAGE"}) + "\n")
    time.sleep(0.2)
    stop.set()
    thread.join(1)

    assert [event["kind"] for event in log.after(-1)] == ["run", "row"]
    assert len(said) == 1 and "could not place the game window" in said[0] and "apt install xdotool" in said[0]


def test_what_a_placement_warns_about_is_said(tmp_path):
    said = []
    log, stop, thread = run_follow(tmp_path, lambda: ({"kind": "layout", "x": 640, "y": 300, "width": 1280, "height": 720}, ["it did not move"]), said)
    (tmp_path / "20991231T000000Z-jev-s1-darwin").mkdir()
    time.sleep(0.3)
    stop.set()
    thread.join(1)

    assert said == ["view: it did not move"] and [event["kind"] for event in log.after(-1)] == ["run", "layout"]


def test_a_placement_that_waits_for_the_window_does_not_stop_the_run_from_being_followed(tmp_path):
    """xdotool search --sync can wait for seconds; the rows of the game must reach the page meanwhile."""
    release = threading.Event()
    log, stop, thread = run_follow(tmp_path, lambda: (release.wait(5), ({"kind": "layout", "x": 0, "y": 0, "width": 1280, "height": 720}, []))[1], [])
    folder = tmp_path / "20991231T000000Z-jev-s1-darwin"
    folder.mkdir()
    time.sleep(0.1)
    (folder / "episode.jsonl").write_text(json.dumps({"t": 0.0, "tactic": "ENGAGE"}) + "\n")
    time.sleep(0.2)
    before = [event["kind"] for event in log.after(-1)]
    release.set()
    time.sleep(0.2)
    stop.set()
    thread.join(1)

    assert before == ["run", "row"]  # the placement had not finished, and the row was served
    assert [event["kind"] for event in log.after(-1)] == ["run", "row", "layout"]


def test_without_a_placer_nothing_is_placed(tmp_path):
    said = []
    log, stop, thread = run_follow(tmp_path, None, said)
    (tmp_path / "20991231T000000Z-jev-s1-darwin").mkdir()
    time.sleep(0.2)
    stop.set()
    thread.join(1)

    assert [event["kind"] for event in log.after(-1)] == ["run"] and said == []


# --- serve and the command -------------------------------------------------------------------------------------------------------------


def test_serve_gives_follow_a_placer_that_uses_the_corner_asked_for(tmp_path, monkeypatch):
    seen = {}

    def fake_follow(log, stop, runs_dir, say=None, place=None):
        seen["place"] = place
        raise RuntimeError("stop here")

    monkeypatch.setattr(view, "follow", fake_follow)
    monkeypatch.setattr(view, "place_game_window", lambda x, y: ({"kind": "layout", "x": x, "y": y, "width": 1280, "height": 720}, []))

    view.serve(0, None, None, runs_dir=tmp_path, say=lambda message: None, place_game=(7, 9))

    assert seen["place"]()[0]["x"] == 7 and seen["place"]()[0]["y"] == 9


def test_serve_places_nothing_unless_asked(tmp_path, monkeypatch):
    seen = {}

    def fake_follow(log, stop, runs_dir, say=None, place=None):
        seen["place"] = place
        raise RuntimeError("stop here")

    monkeypatch.setattr(view, "follow", fake_follow)
    view.serve(0, None, None, runs_dir=tmp_path, say=lambda message: None)

    assert seen["place"] is None
