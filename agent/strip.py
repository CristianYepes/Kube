"""Spec 003: the strip that `kube-agent run --strip` puts over the game window, so that a video shows who is playing (the
rule bot or Jev, not a person), the tactic in force and the keys being pressed.

It reads the run folder while the agent writes it: `decisions.jsonl` (a row per decision, every half second),
`keys.jsonl` (a row each time the keys sent to the game change; the agent writes it only with --strip) and `result.json`
(written last). It runs with the system Python, which has GTK: the Tk of uv's Python draws X11 bitmap fonts (seen on the
owner's Linux, 2026-10-11). The agent starts it with the credentials taken out of its environment; it makes no network
call.

    usage: python3 agent/strip.py RUN_FOLDER {idle,jev,scripted}
"""

import argparse
import json
import os
import signal
import sys
from pathlib import Path

POLL_MS = 30  # the keys change several times a second; 30 ms is under two frames of a 60 fps video
LINGER_SECONDS = 3  # the agent closes the game as soon as it ends; the result stays a moment longer
MARGIN_PX = 24
TACTICS = ("ENGAGE", "KITE", "RETREAT", "SEARCH")  # the agent's (kube_agent/controller.py); a test keeps them equal
WHAT = {  # short forms of the `what` of each option in the question Jev is asked (kube_agent/config.py)
    "ENGAGE": "stands and shoots",
    "KITE": "backs off, shooting",
    "RETREAT": "runs to open space",
    "SEARCH": "looks for the rest",
}
PLAYERS = {"idle": "NO ONE IS PLAYING", "jev": "JEV IS PLAYING", "scripted": "THE RULE BOT IS PLAYING"}
# The seven flags of the agent's `C` line, in the order the controller writes them and the game reads them
# (kube_agent/controller.py, sources/jev/agent_cmd.c), named as the keys a person would press: forward, back,
# strafe left, strafe right, turn left, turn right, fire.
KEYS = ("W", "S", "A", "D", "←", "→", "↑")
ENDINGS = {"win": "WON in {:.1f} s", "lose": "LOST at {:.1f} s", "timeout": "TIME UP at {:.1f} s"}
INSTALL_HINT = "sudo apt install python3-gi gir1.2-gtk-3.0"
STYLE = b"""
window { background-color: #121212; }
label { font-family: Ubuntu, sans-serif; color: #ececec; }
.who { color: #8c8c8c; font-size: 14px; }
.tactic { font-size: 22px; font-weight: bold; }
.what { color: #8c8c8c; font-size: 16px; }
.key { color: #8c8c8c; font-size: 15px; border: 2px solid #3a3a3a; border-radius: 6px; min-width: 30px; min-height: 30px; }
.key.on { color: #121212; background-color: #ececec; border-color: #ececec; }
"""


def held_keys(line: str) -> frozenset:
    """The keys a `C` line holds down: "C 1 0 0 0 0 1 1" holds W, → and ↑."""
    parts = line.split(" ")
    if len(parts) != 8 or parts[0] != "C" or any(flag not in ("0", "1") for flag in parts[1:]):
        raise ValueError(f"not a C line with seven 0/1 flags: {line!r}")
    return frozenset(key for key, flag in zip(KEYS, parts[1:]) if flag == "1")


class Tail:
    """The new complete lines of a JSON-lines file that another process is still writing."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._offset = 0
        self._line = 0

    def read(self) -> tuple:
        """(rows, problems): the rows of the lines completed since the last read, and the lines that did not parse.
        A line that is half written is left for the next read."""
        try:
            with self.path.open("rb") as file:
                file.seek(self._offset)
                data = file.read()
        except FileNotFoundError:
            return [], []
        complete = data[: data.rfind(b"\n") + 1]
        self._offset += len(complete)
        rows, problems = [], []
        for raw in complete.splitlines():
            self._line += 1
            if not raw.strip():
                continue
            try:
                rows.append(json.loads(raw))
            except ValueError as error:
                problems.append(f"{self.path.name} line {self._line}: {error}")
        return rows, problems


def read_result(path: Path):
    """result.json once it is whole, else None: the agent writes it last, and a poll can catch it half written."""
    try:
        return json.loads(path.read_text())
    except (FileNotFoundError, ValueError):
        return None


def ending_of(result: dict) -> str:
    ending = ENDINGS.get(result.get("outcome"))
    return ending.format(result["survival_seconds"]) if ending else "STOPPED"  # an error: the agent's terminal says which


class Strip:
    """What the strip says, from the rows read so far."""

    def __init__(self, policy: str) -> None:
        self.who = PLAYERS[policy]
        self.tactic = None
        self.keys = frozenset()
        self.ending = None
        self.problems = []

    @property
    def ended(self) -> bool:
        return self.ending is not None

    def take(self, decisions: list, keys: list, result) -> bool:
        """Take the rows read since the last call; True when what the strip shows changes."""
        before = (self.tactic, self.keys, self.ending)
        for row in decisions:
            if row.get("applied") and row.get("tactic") in TACTICS:
                self.tactic = row["tactic"]
        for row in keys:
            try:
                self.keys = held_keys(row["keys"])
            except (KeyError, TypeError, ValueError) as error:
                self.problems.append(f"keys.jsonl: a row without a valid C line ({type(error).__name__}: {error})")
        if result is not None:
            self.ending, self.keys = ending_of(result), frozenset()
        return (self.tactic, self.keys, self.ending) != before

    def line(self) -> tuple:
        """The words of the second row: the big one, and the one after it."""
        if self.ending is not None:
            return self.ending, ""
        if self.tactic is None:
            return "", "the game is starting"
        return self.tactic, WHAT[self.tactic]


def bottom_left(area_x: int, area_y: int, area_height: int, strip_height: int, margin: int = MARGIN_PX) -> tuple:
    """The top left corner that puts the strip `margin` pixels in from the bottom left corner of the area."""
    return area_x + margin, area_y + area_height - strip_height - margin


def show(run_dir: Path, policy: str) -> int:
    # Only X11 lets a window that no window manager handles (a popup) be put at a given place and stay above the
    # others; GNOME on Wayland runs X11 programs, the game among them, through Xwayland. It must be set before GTK loads.
    os.environ["GDK_BACKEND"] = "x11"
    try:
        import gi
        gi.require_version("Gdk", "3.0")
        gi.require_version("Gtk", "3.0")
        from gi.repository import Gdk, GLib, Gtk
    except (ImportError, ValueError) as error:
        print(f"strip: GTK 3 for Python is not available ({error}); install it with: {INSTALL_HINT}", file=sys.stderr)
        return 1
    if not Gtk.init_check(sys.argv)[0]:
        print(f"strip: cannot open the display {os.environ.get('DISPLAY')!r}; the game and the strip need DISPLAY=:0",
              file=sys.stderr)
        return 1

    style = Gtk.CssProvider()
    style.load_from_data(STYLE)
    Gtk.StyleContext.add_provider_for_screen(Gdk.Screen.get_default(), style, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

    def label(text: str, css_class: str, xalign: float = 0.5):
        widget = Gtk.Label(label=text, xalign=xalign)
        widget.get_style_context().add_class(css_class)
        return widget

    strip = Strip(policy)
    tactic, what = label("", "tactic", 0.0), label("", "what", 0.0)
    what.set_width_chars(max(len(text) for text in WHAT.values()))  # the strip keeps its width as the words change
    for word in (tactic, what):
        word.set_valign(Gtk.Align.BASELINE)
    words = Gtk.Box(spacing=12)
    words.pack_start(tactic, False, False, 0)
    words.pack_start(what, False, False, 0)
    left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8, valign=Gtk.Align.CENTER)
    left.pack_start(label(strip.who, "who", 0.0), False, False, 0)
    left.pack_start(words, False, False, 0)

    keys = {name: label(name, "key") for name in KEYS}
    row = Gtk.Box(spacing=32)
    row.pack_start(left, False, False, 0)
    for top, bottom in (("W", ("A", "S", "D")), ("↑", ("←", None, "→"))):  # the two clusters of a keyboard
        cluster = Gtk.Grid(column_spacing=6, row_spacing=6, valign=Gtk.Align.CENTER)
        cluster.attach(keys[top], 1, 0, 1, 1)
        for column, name in enumerate(bottom):
            if name is not None:
                cluster.attach(keys[name], column, 1, 1, 1)
        row.pack_start(cluster, False, False, 0)

    def render() -> None:
        big, small = strip.line()
        tactic.set_text(big)
        what.set_text(small)
        for name, key in keys.items():
            if name in strip.keys:
                key.get_style_context().add_class("on")
            else:
                key.get_style_context().remove_class("on")

    window = Gtk.Window(type=Gtk.WindowType.POPUP)
    window.set_border_width(16)
    window.add(row)
    render()
    _, natural = window.get_preferred_size()
    display = Gdk.Display.get_default()
    area = (display.get_primary_monitor() or display.get_monitor(0)).get_workarea()
    window.move(*bottom_left(area.x, area.y, area.height, natural.height))
    window.show_all()

    decisions, key_rows = Tail(run_dir / "decisions.jsonl"), Tail(run_dir / "keys.jsonl")
    agent = os.getppid()
    reported = 0

    def poll() -> bool:
        nonlocal reported
        new_decisions, decision_problems = decisions.read()
        new_keys, key_problems = key_rows.read()
        if strip.take(new_decisions, new_keys, read_result(run_dir / "result.json")):
            render()
        for problem in decision_problems + key_problems + strip.problems[reported:]:
            print(f"strip: {problem}", file=sys.stderr)
        reported = len(strip.problems)
        if strip.ended:
            GLib.timeout_add_seconds(LINGER_SECONDS, Gtk.main_quit)
            return False
        if os.getppid() != agent:  # the agent is gone without a result.json: stopped with Ctrl-C, or killed
            Gtk.main_quit()
            return False
        return True

    GLib.timeout_add(POLL_MS, poll)
    signal.signal(signal.SIGINT, signal.SIG_DFL)  # GTK's loop would not see Ctrl-C otherwise
    Gtk.main()
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="strip.py", description="The strip over the game window (spec 003).")
    parser.add_argument("run_folder", type=Path, help="the folder kube-agent run is writing")
    parser.add_argument("policy", choices=sorted(PLAYERS))
    args = parser.parse_args(argv)
    return show(args.run_folder, args.policy)


if __name__ == "__main__":
    sys.exit(main())
