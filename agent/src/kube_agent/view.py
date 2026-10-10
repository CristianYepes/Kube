"""Spec 003: `kube-agent view`. The events from a run folder that is being written or from a finished one, and the
server that hands them, with one page, to a browser on this machine.

The agent flushes every row of `episode.jsonl` and `decisions.jsonl` as it plays (episode.py, `write_row`), so a
separate process can read them while the game runs and the agent's loop is never touched. This module turns the rows
into the few events the page draws. It sends no milliseconds, no cost and no raw state: the page can only show what is
here (specs/003-visual-pass/spec.md, design rule 7).
"""

import json
import os
import re
import subprocess
import sys
import threading
import time
from collections.abc import Callable
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs

from kube_agent.config import RUNS_DIR
from kube_agent.controller import TACTICS
from kube_agent.policies import scripted_tactic

FOLLOW_POLL_SECONDS = 0.025  # how often the live mode looks at the run folder
PAGE_POLL_SECONDS = 0.05  # how often the page asks for new events (plan.md)
UNREADABLE_RESULT_POLLS = 80  # polls of a result.json that does not parse (2 s) before it is reported
MAX_FACTS = 3
GAME_WIDTH, GAME_HEIGHT = 1280, 720  # the drawing area of the game: the page is drawn around a window of this size
GAME_WINDOW_NAME = "^cub3D$"  # a regular expression, for `xdotool search --name`
PLACE_TIMEOUT_SECONDS = 10.0  # for each call to xdotool or xwininfo, and for the window to appear
PLACE_SETTLE_SECONDS = 0.3  # a window manager moves a window a moment after being asked
PLACE_TOLERANCE_PX = 100  # how far from the corner asked for the drawing area may be: a title bar and a border are not a problem
INSTALL_HINT = {"xdotool": "sudo apt install xdotool", "xwininfo": "sudo apt install x11-utils"}
DEFAULT_PORT = 8765
PAGE_DIR = Path(__file__).resolve().parent / "view_page"
CONCLUSION_PATH = Path(__file__).resolve().parent / "view_conclusion.json"
FONT_FILES = ("IBMPlexSans-Regular.woff2", "IBMPlexSans-SemiBold.woff2", "IBMPlexMono-Regular.woff2", "IBMPlexMono-SemiBold.woff2")
# The page is one file with its own style and script. It loads its fonts from here and asks only this server.
CONTENT_SECURITY_POLICY = ("default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; font-src 'self'; "
                           "connect-src 'self'; frame-ancestors 'none'")
RUN_NAME = re.compile(r"^(\d{8}T\d{6}Z)-(idle|scripted|jev)-s(\d+)-[a-z0-9]+$")  # `kube-agent run`'s folders only


# --- what Jev read, as a few short facts --------------------------------------------------------------------------------


def describe_state(state: dict) -> list[str]:
    """At most three short facts of the state Jev was sent, nearest threat first.

    Every word is a value of `features.semantic_state` or one of the fixed phrases below: nothing is generated.
    """
    threats, nearest = state["threats"], state["threats"]["nearest"]
    if nearest is None:
        return ["no zombie left"]
    facts = [f"{nearest['kind']}, {nearest['distance']}, {nearest['direction']}"]
    if state["player"]["being_hit"]:
        facts.append("being hit")
    if state["space"]["cornered"]:
        facts.append("cornered")
    if state["player"]["health"] != "high":
        facts.append(f"health {state['player']['health']}")
    facts.append(f"{threats['in_view']} in view, {threats['remaining']} left")
    return facts[:MAX_FACTS]


# --- events -------------------------------------------------------------------------------------------------------------


def run_event(name: str, mode: str) -> dict:
    match = RUN_NAME.match(name)
    if match is None:
        raise ValueError(f"{name!r} is not the name of a run folder (UTC time, policy, seed, machine)")
    return {"kind": "run", "run_id": name, "policy": match.group(2), "seed": int(match.group(3)), "mode": mode}


def row_event(row: dict) -> dict:
    return {"kind": "row", "t": row["t"], "tactic": row["tactic"]}


def decision_event(row: dict) -> dict:
    """One decision of `decisions.jsonl`, with what the four rules would have chosen from the same state."""
    reason, answered_at = row.get("reason"), row.get("answered_at")
    if answered_at is None and reason != "episode_ended":
        answered_at = row["t"]  # the rules decide at once; an answer that came after the end was never read
    state = row["state"]
    return {
        "kind": "decision",
        "t": row["t"],
        "answered_at": answered_at,
        "source": row.get("source", "scripted"),
        "tactic": row["tactic"],
        "applied": row["applied"],
        "reason": reason,
        "probabilities": _probabilities(row),
        "rules": scripted_tactic(state),
        "read": describe_state(state),
    }


def _probabilities(row: dict) -> dict[str, float] | None:
    raw = ((row.get("answers") or {}).get("tactic") or {}).get("probabilities")
    if not raw:
        return None
    return {tactic: round(float(raw.get(tactic, 0.0)), 3) for tactic in TACTICS}


def end_event(result: dict) -> dict:
    return {"kind": "end", "outcome": result["outcome"], "survival_seconds": result["survival_seconds"],
            "damage_taken": result["damage_taken"]}


class EventLog:
    """The events so far, numbered from 0. The server hands them to the page by number."""

    def __init__(self) -> None:
        self._events: list[dict] = []
        self._lock = threading.Lock()

    def append(self, event: dict) -> int:
        with self._lock:
            number = len(self._events)
            self._events.append({"n": number, **event})
        return number

    def after(self, number: int) -> list[dict]:
        """The events numbered above `number` (-1 gives all of them)."""
        with self._lock:
            return self._events[max(number, -1) + 1:]


# --- reading a folder that is still being written -------------------------------------------------------------------------


class RunReader:
    """Reads the new complete lines of one run folder, poll after poll.

    A line that is half written is left for the next poll. A line that cannot be read is not served, and is
    listed in `problems`, so that whoever runs the view can see it.
    """

    def __init__(self, folder: Path) -> None:
        self.folder = folder
        self.ended = False
        self.problems: list[str] = []
        self._offset = {"episode.jsonl": 0, "decisions.jsonl": 0}
        self._line = {"episode.jsonl": 0, "decisions.jsonl": 0}
        self._unreadable_result_polls = 0

    def read_new(self) -> list[dict]:
        if self.ended:
            return []
        # result.json is looked at FIRST: the agent writes it last, so every row written before it is read below,
        # and the end event can never come before a row that was already there.
        result = self._read_result()
        events = self._read_lines("episode.jsonl", row_event) + self._read_lines("decisions.jsonl", decision_event)
        if result is not None:
            events.append(result)
            self.ended = True
        return events

    def _read_lines(self, name: str, make: Callable[[dict], dict]) -> list[dict]:
        try:
            with (self.folder / name).open("rb") as file:
                file.seek(self._offset[name])
                data = file.read()
        except FileNotFoundError:
            return []
        complete = data[: data.rfind(b"\n") + 1]
        self._offset[name] += len(complete)
        events = []
        for raw in complete.splitlines():
            self._line[name] += 1
            if not raw.strip():
                continue
            try:
                events.append(make(json.loads(raw)))
            except (ValueError, KeyError, TypeError) as error:
                self.problems.append(f"{name} line {self._line[name]} of {self.folder.name}: {type(error).__name__}: {error}")
        return events

    def _read_result(self) -> dict | None:
        try:
            text = (self.folder / "result.json").read_text()
        except FileNotFoundError:
            return None
        try:
            return end_event(json.loads(text))
        except (ValueError, KeyError, TypeError) as error:  # most often a file that is being written: the next poll reads it
            self._unreadable_result_polls += 1
            if self._unreadable_result_polls == UNREADABLE_RESULT_POLLS:
                self.problems.append(f"result.json of {self.folder.name} is still unreadable after {UNREADABLE_RESULT_POLLS} polls: "
                                     f"{type(error).__name__}: {error}")
            return None


# --- putting the game window where the page expects it -----------------------------------------------------------------------


class PlacementError(Exception):
    """The game's window could not be found, moved or measured."""


def _run_tool(run: Callable, argv: list[str], timeout: float) -> str:
    try:
        done = run(argv, capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        raise PlacementError(f"{argv[0]} is not installed ({INSTALL_HINT[argv[0]]})") from None
    except subprocess.TimeoutExpired:
        raise PlacementError(f"`{' '.join(argv)}` did not finish in {timeout:g} s") from None
    if done.returncode != 0:
        raise PlacementError(f"`{' '.join(argv)}` failed with exit code {done.returncode}: {done.stderr.strip()[:200] or 'no message'}")
    return done.stdout


def _measure(info: str, label: str) -> int:
    match = re.search(rf"^\s*{label}:\s*(-?\d+)\s*$", info, re.M)
    if match is None:
        raise PlacementError(f"the answer of xwininfo has no '{label}' line")
    return int(match.group(1))


def place_game_window(x: int, y: int, run: Callable = subprocess.run, sleep: Callable[[float], object] = time.sleep,
                      timeout: float = PLACE_TIMEOUT_SECONDS) -> tuple[dict, list[str]]:
    """Move the game's window towards (x, y) and say where its drawing area really is, in screen pixels (X11 only).

    What a window manager does with a move is its own business (a title bar, a border, a refusal), so the layout is read
    back with xwininfo and the page follows the window, not the other way round. Returns the layout event and what to warn about.
    """
    windows = _run_tool(run, ["xdotool", "search", "--sync", "--name", GAME_WINDOW_NAME], timeout).split()
    if not windows:
        raise PlacementError(f"no window named cub3D appeared in {timeout:g} s")
    window = windows[-1]  # the newest, if an old one is still open
    _run_tool(run, ["xdotool", "windowmove", window, str(x), str(y)], timeout)
    sleep(PLACE_SETTLE_SECONDS)
    info = _run_tool(run, ["xwininfo", "-id", window], timeout)
    layout = {"kind": "layout", "x": _measure(info, "Absolute upper-left X"), "y": _measure(info, "Absolute upper-left Y"),
              "width": _measure(info, "Width"), "height": _measure(info, "Height")}
    warnings = []
    if abs(layout["x"] - x) > PLACE_TOLERANCE_PX or abs(layout["y"] - y) > PLACE_TOLERANCE_PX:
        warnings.append(f"the drawing area is at {layout['x']},{layout['y']}, far from {x},{y}: this session may not let the window be moved "
                        f"(Wayland?). The page follows the window, but 1920x1080 from there must fit on the screen")
    if (layout["width"], layout["height"]) != (GAME_WIDTH, GAME_HEIGHT):
        warnings.append(f"the drawing area is {layout['width']}x{layout['height']} and the page is drawn for {GAME_WIDTH}x{GAME_HEIGHT}")
    return layout, warnings


def _place_in_background(log: EventLog, place: Callable[[], tuple[dict, list[str]]], say: Callable[[str], None]) -> None:
    try:
        layout, warnings = place()
    except PlacementError as error:
        say(f"view: could not place the game window: {error}")
        return
    for warning in warnings:
        say(f"view: {warning}")
    log.append(layout)


# --- the live mode ----------------------------------------------------------------------------------------------------------


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _newest_run(runs_dir: Path, since: str) -> str | None:
    try:
        names = os.listdir(runs_dir)
    except FileNotFoundError:
        return None
    return max((name for name in names if (match := RUN_NAME.match(name)) and match.group(1) >= since), default=None)


def _say(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


def follow(log: EventLog, stop: threading.Event, runs_dir: Path = RUNS_DIR, since: str | None = None,
           say: Callable[[str], None] = _say, place: Callable[[], tuple[dict, list[str]]] | None = None) -> None:
    """Follow the newest run folder created at or after `since` (default: now) until `stop` is set.

    One call serves many runs: when a newer folder appears it starts a new run event. Folders of evaluations and
    probes are not runs of `kube-agent run` and are left alone. With `place`, each new run also gets, a moment later,
    a layout event with the place of its game window (the call waits for the window, so it runs apart from the polling).
    """
    since = since or utc_stamp()
    current, reader, reported = None, None, 0
    while not stop.is_set():
        newest = _newest_run(runs_dir, since)
        if newest is not None and newest != current:
            log.append(run_event(newest, "live"))
            current, reader, reported = newest, RunReader(runs_dir / newest), 0
            if place is not None:
                threading.Thread(target=_place_in_background, args=(log, place, say), daemon=True).start()
        if reader is not None:
            for event in reader.read_new():
                log.append(event)
            for problem in reader.problems[reported:]:
                say(f"view: {problem}")
            reported = len(reader.problems)
        stop.wait(FOLLOW_POLL_SECONDS)


# --- the replay of a finished folder ----------------------------------------------------------------------------------------


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.is_file() else []


def replay_schedule(folder: Path) -> list[tuple[float, dict]]:
    """Every event of a finished folder with the game time at which it happened, in order.

    A decision is released at the moment its answer was read (`answered_at`), an episode row at its own time,
    the end at `survival_seconds`. An answer that arrived after the episode had ended was never read by anyone:
    it goes just before the end.
    """
    result_path = folder / "result.json"
    end = end_event(json.loads(result_path.read_text())) if result_path.is_file() else None
    rows = _jsonl(folder / "episode.jsonl")
    end_at = end["survival_seconds"] if end else (rows[-1]["t"] if rows else 0.0)

    schedule = [(row["t"], row_event(row)) for row in rows]
    for row in _jsonl(folder / "decisions.jsonl"):
        event = decision_event(row)
        schedule.append((event["answered_at"] if event["answered_at"] is not None else end_at, event))
    schedule.sort(key=lambda item: item[0])  # stable: at the same moment, the order of the files
    schedule.insert(0, (0.0, run_event(folder.name, "replay")))
    if end:
        schedule.append((end_at, end))
    return schedule


def replay(log: EventLog, folder: Path, stop: threading.Event, until: float | None = None,
           clock: Callable[[], float] = time.monotonic, wait: Callable[[float], object] | None = None) -> None:
    """Release a finished folder's events at their real speed. With `until`, stop there: the page stays frozen."""
    wait = wait or stop.wait
    start = clock()
    for at, event in replay_schedule(folder):
        if until is not None and at > until:
            return
        remaining = at - (clock() - start)
        if remaining > 0:
            wait(remaining)
        if stop.is_set():
            return
        log.append(event)


# --- the server --------------------------------------------------------------------------------------------------------------


class _Handler(BaseHTTPRequestHandler):
    """Serves the page, its four fonts, the conclusion card and the events. Nothing else, and only GET."""

    log: EventLog  # set by make_server

    def version_string(self) -> str:
        return "kube-view"

    def log_message(self, format: str, *args) -> None:  # the page asks 20 times a second: no line per request
        pass

    def do_GET(self) -> None:
        if not self._host_is_ours():  # DNS rebinding: a page on another site whose name points here must not read the run
            return self._reply(404, b"not found\n", "text/plain; charset=utf-8")
        path, _, query = self.path.partition("?")
        font = path.removeprefix("/fonts/") if path.startswith("/fonts/") else None
        if path == "/":
            self._file(PAGE_DIR / "index.html", "text/html; charset=utf-8")
        elif path == "/conclusion":
            self._file(CONCLUSION_PATH, "application/json")
        elif font in FONT_FILES:  # a name from this list, never a path made from the request
            self._file(PAGE_DIR / "fonts" / font, "font/woff2")
        elif path == "/events":
            self._events(query)
        else:
            self._reply(404, b"not found\n", "text/plain; charset=utf-8")

    def _method_not_allowed(self) -> None:
        self._reply(405, b"only GET\n", "text/plain; charset=utf-8", {"Allow": "GET"})

    do_POST = do_PUT = do_DELETE = do_PATCH = do_OPTIONS = do_HEAD = _method_not_allowed

    def _host_is_ours(self) -> bool:
        port = self.server.server_address[1]
        return self.headers.get("Host", "") in (f"127.0.0.1:{port}", f"localhost:{port}")

    def _events(self, query: str) -> None:
        values = parse_qs(query, keep_blank_values=True).get("after", ["-1"])
        if len(values) != 1 or not re.fullmatch(r"-?\d{1,12}", values[0]):
            return self._reply(400, b"after must be a whole number\n", "text/plain; charset=utf-8")
        self._reply(200, json.dumps(self.log.after(int(values[0]))).encode(), "application/json")

    def _file(self, path: Path, content_type: str) -> None:
        try:
            body = path.read_bytes()
        except FileNotFoundError:
            return self._reply(404, b"not found\n", "text/plain; charset=utf-8")
        self._reply(200, body, content_type)

    def _reply(self, status: int, body: bytes, content_type: str, extra: dict[str, str] | None = None) -> None:
        self.send_response(status)
        headers = {"Content-Type": content_type, "Content-Length": str(len(body)), "Cache-Control": "no-store",
                   "X-Content-Type-Options": "nosniff", "Referrer-Policy": "no-referrer",
                   "Content-Security-Policy": CONTENT_SECURITY_POLICY, **(extra or {})}
        for name, value in headers.items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)


def make_server(log: EventLog, port: int = DEFAULT_PORT) -> ThreadingHTTPServer:
    """A server on 127.0.0.1 only. It is already listening when this returns; the caller runs `serve_forever`."""
    try:
        server = ThreadingHTTPServer(("127.0.0.1", port), type("Handler", (_Handler,), {"log": log}))
    except OSError as error:
        raise OSError(error.errno, f"cannot listen on 127.0.0.1:{port}: {error.strerror}") from error
    server.daemon_threads = True
    return server


def serve(port: int, replay_folder: Path | None = None, until: float | None = None, runs_dir: Path = RUNS_DIR,
          say: Callable[[str], None] = _say, on_ready: Callable[[ThreadingHTTPServer], None] | None = None,
          place_game: tuple[int, int] | None = None) -> int:
    """Serve the view until it is interrupted: the newest live run, or a replay of `replay_folder`. Returns the exit code.

    With `place_game` = (x, y), the window of each live game is moved towards that corner of the screen (X11 only)."""
    if replay_folder is not None:
        replay_schedule(replay_folder)  # a folder that is not a run, or a file that cannot be read, fails here, before anything starts
    log, stop = EventLog(), threading.Event()
    server = make_server(log, port)
    failures: list[Exception] = []

    def work() -> None:
        try:
            if replay_folder is not None:
                replay(log, replay_folder, stop, until)
            else:
                follow(log, stop, runs_dir, say=say, place=(lambda: place_game_window(*place_game)) if place_game else None)
        except Exception as error:  # nothing would feed the page any more: say so and stop, rather than serve a frozen page
            failures.append(error)
            say(f"view: stopped: {type(error).__name__}: {error}")
            server.shutdown()

    worker = threading.Thread(target=work, daemon=True)
    worker.start()
    say(f"view: open http://127.0.0.1:{server.server_address[1]} in a browser, full screen (F11) and at 100% zoom, so that the page lines up "
        f"with the game window  (Ctrl-C to stop)")
    if on_ready:
        on_ready(server)
    try:
        server.serve_forever(poll_interval=0.1)
    except KeyboardInterrupt:
        say("view: stopped")
    finally:
        stop.set()
        server.server_close()
        worker.join(2)
    return 1 if failures else 0
