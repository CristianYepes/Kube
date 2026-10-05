#!/usr/bin/env python3
"""Checks of the C bridge in sources/jev/ (spec 002): what cub3D_agent prints, and the
commands it obeys.

Standard library only, so it runs where the game runs: inside the kube-dev
container (Python 3.10, no uv) and on native Linux alike.

    docker exec -e DISPLAY=:99 -w /kube kube-dev python3 agent/check_bridge.py   # Mac
    DISPLAY=:99 python3 agent/check_bridge.py                                    # Linux

It starts ./agent/cub3D_agent itself, with stdin open and silent unless a check
sends commands (EOF would make the game quit), and reads its stdout as it comes.
It prints PASS or FAIL per check and exits 1 if any failed. Build the binary
first: make -C agent
"""
import json
import math
import os
import pty
import select
import signal
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BINARY = os.path.join(ROOT, "agent", "cub3D_agent")
MAP = "maps/bonus/subject_map.cub"
MINIMAL_MAP = "maps/good/minimal.cub"
SEED = 1

# The contract of plan.md, "Contracts": fields, in this order.
INIT_KEYS = ["type", "map", "width", "height", "seed"]
OBS_KEYS = ["type", "frame", "t", "dt", "state", "wave", "hp", "weapon_ready",
            "player", "drops", "enemies"]
PLAYER_KEYS = ["x", "y", "dx", "dy"]
ENEMY_KEYS = ["x", "y", "type", "hp", "ai", "los"]
FACING = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
TERRAIN = str.maketrans("NSEW ", "00001")  # start cells become floor, spaces walls
MAP_IDENTIFIERS = ("NO", "SO", "WE", "EA", "F", "C")

# What the game does per second of its own clock (includes/cub3d.h).
MOVE_SPEED = 1.2       # cells per second, forward and back
PLANE_LENGTH = 0.66    # |plane| (set_ns): strafing moves along plane, not a unit vector
STRAFE_SPEED = MOVE_SPEED * PLANE_LENGTH   # 0.792 cells per second
TURN_SPEED = 1.8       # radians per second
FIRE_COOLDOWN = 0.6    # seconds
FPS_ON_MINIMAL = 75.0  # frames per second measured for spec 001 (baseline file)
STOP = "C 0 0 0 0 0 0 0\n"


class Run:
    """What one run of the game printed."""

    def __init__(self, lines, stderr, alive_at_end):
        self.lines = lines
        self.stderr = stderr
        self.alive_at_end = alive_at_end


class Game:
    """cub3D_agent with both ends piped: commands go in, observation lines come out."""

    def __init__(self, map_path=MAP, seed=SEED):
        self.stderr = tempfile.TemporaryFile()
        self.proc = subprocess.Popen([BINARY, map_path, str(seed)], cwd=ROOT,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=self.stderr)
        self.fd = self.proc.stdout.fileno()
        self.buffer = b""
        self.lines = []
        self.eof = False

    def read(self, seconds):
        """Read what arrives for `seconds`, or until the game exits."""
        deadline = time.monotonic() + seconds
        while not self.eof and time.monotonic() < deadline:
            wait = min(0.5, max(0.0, deadline - time.monotonic()))
            ready, _, _ = select.select([self.fd], [], [], wait)
            if not ready:
                continue
            chunk = os.read(self.fd, 65536)
            if not chunk:
                self.eof = True  # the game exited
                break
            self.buffer += chunk
            *whole, self.buffer = self.buffer.split(b"\n")
            self.lines.extend(whole)

    def start(self, timeout=15.0):
        """Read until the init line and a first observation are in. False if they never are."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline and not self.eof:
            self.read(0.2)
            if len(self.lines) >= 2:
                return True
        return False

    def send(self, text):
        """Write raw text to the game's stdin."""
        self.proc.stdin.write(text.encode())
        self.proc.stdin.flush()

    def finish(self):
        """Stop the game and return what it printed."""
        alive = self.proc.poll() is None
        self.proc.terminate()
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
            self.proc.wait()
        self.proc.stdout.close()
        try:
            self.proc.stdin.close()
        except OSError:
            pass  # the game is gone and a byte was still waiting: nothing to save
        self.stderr.seek(0)
        return Run(self.lines, self.stderr.read().decode(errors="replace"), alive)


def run_game(seconds, stall=0.0):
    """Run cub3D_agent for `seconds`. The first `stall` seconds nothing is read."""
    game = Game()
    time.sleep(stall)
    game.read(seconds - stall)
    return game.finish()


def parse(run):
    """The JSON records of a run, and a message for every line that is not JSON."""
    records, bad = [], []
    for number, raw in enumerate(run.lines, 1):
        try:
            records.append(json.loads(raw))
        except ValueError:
            bad.append("line %d is not JSON: %r" % (number, raw[:60]))
    return records, bad


def observations(lines):
    """The observation records among raw lines. Lines that are not JSON are skipped
    here: the first checks report them."""
    found = []
    for raw in lines:
        try:
            record = json.loads(raw)
        except ValueError:
            continue
        if isinstance(record, dict) and record.get("type") == "obs":
            found.append(record)
    return found


def read_map_file(path):
    """The map rows of a .cub file, read here and not by the game's own parser."""
    rows, in_map = [], False
    with open(path) as handle:
        for line in handle:
            line = line.rstrip("\r\n")
            if not in_map:
                words = line.split()
                if not words or words[0] in MAP_IDENTIFIERS:
                    continue
                in_map = True
            rows.append(line)
    while rows and not rows[-1].strip():
        rows.pop()
    return rows


def find_start(rows):
    """Where the player starts: the middle of the N, S, E or W cell, and facing."""
    for y, row in enumerate(rows):
        for x, char in enumerate(row):
            if char in FACING:
                return x + 0.5, y + 0.5, FACING[char]
    return None


def is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def is_float(value):
    return isinstance(value, float)


def validate_obs(obs):
    """Every way one observation breaks the contract."""
    if not isinstance(obs, dict) or list(obs) != OBS_KEYS:
        return ["fields are %s" % (list(obs) if isinstance(obs, dict) else obs)]
    problems = []
    for key in ("frame", "state", "wave", "hp", "weapon_ready", "drops"):
        if not is_int(obs[key]):
            problems.append("%s is not an integer: %r" % (key, obs[key]))
    for key in ("t", "dt"):
        if not is_float(obs[key]):
            problems.append("%s is not a decimal number: %r" % (key, obs[key]))
    for key, allowed in (("state", (0, 1, 2)), ("wave", (1, 2, 3)),
                         ("weapon_ready", (0, 1))):
        if obs[key] not in allowed:
            problems.append("%s is %r, expected one of %s" % (key, obs[key], allowed))
    player = obs["player"]
    if not isinstance(player, dict) or list(player) != PLAYER_KEYS:
        problems.append("player fields are %r" % (player,))
    else:
        problems += ["player.%s is not a decimal number" % k
                     for k in PLAYER_KEYS if not is_float(player[k])]
    if not isinstance(obs["enemies"], list):
        return problems + ["enemies is not a list"]
    for enemy in obs["enemies"]:
        problems += validate_enemy(enemy)
    return problems


def validate_enemy(enemy):
    if not isinstance(enemy, dict) or list(enemy) != ENEMY_KEYS:
        return ["enemy fields are %r" % (enemy,)]
    problems = ["enemy.%s is not a decimal number" % k
                for k in ("x", "y") if not is_float(enemy[k])]
    for key, allowed in (("type", (0, 1, 2)), ("ai", (0, 1, 2)), ("los", (0, 1))):
        if not is_int(enemy[key]) or enemy[key] not in allowed:
            problems.append("enemy.%s is %r, expected one of %s"
                            % (key, enemy[key], allowed))
    if not is_int(enemy["hp"]) or enemy["hp"] < 1:
        problems.append("enemy.hp is %r, expected an integer from 1" % (enemy["hp"],))
    return problems


# ------------------------------------------------- the observations (T3b): the checks
# Each check returns (problems, notes). No problem means PASS.

def check_init(records, expected):
    if not records:
        return ["the game printed nothing"], []
    init = records[0]
    if not isinstance(init, dict) or list(init) != INIT_KEYS:
        return ["init fields are %r, expected %s" % (init, INIT_KEYS)], []
    width = max(len(row) for row in expected)
    # The game turns spaces into walls, pads short rows with walls, and turns the
    # player's start cell into floor (set_player_at); the first observation says
    # where the player starts.
    want = [row.translate(TERRAIN).ljust(width, "1") for row in expected]
    problems = []
    if init["type"] != "init":
        problems.append("type is %r" % init["type"])
    if init["width"] != width or init["height"] != len(expected):
        problems.append("size is %sx%s, the file says %dx%d"
                        % (init["width"], init["height"], width, len(expected)))
    if init["seed"] != SEED:
        problems.append("seed is %r, expected %d" % (init["seed"], SEED))
    for number, (got, wanted) in enumerate(zip(init["map"], want)):
        if got != wanted:
            problems.append("map row %d is %r, the file says %r" % (number, got, wanted))
            break
    if len(init["map"]) != len(want):
        problems.append("%d map rows, the file has %d" % (len(init["map"]), len(want)))
    return problems, ["%d rows of %d columns, compared with the file read here"
                      % (len(expected), width)]


def check_first_obs(obs, expected):
    if not obs:
        return ["no observation"], []
    first = obs[0]
    start_x, start_y, (face_x, face_y) = find_start(expected)
    problems = []
    for key, want in (("frame", 1), ("state", 0), ("wave", 1), ("hp", 100),
                      ("weapon_ready", 1)):
        if first.get(key) != want:
            problems.append("%s is %r, expected %r" % (key, first.get(key), want))
    player = first.get("player", {})
    for key, want in (("x", start_x), ("y", start_y), ("dx", face_x), ("dy", face_y)):
        if abs(player.get(key, 1e9) - want) > 0.001:
            problems.append("player.%s is %r, expected %s" % (key, player.get(key), want))
    enemies = first.get("enemies", [])
    if len(enemies) != 3:
        problems.append("%d enemies in wave 1, expected 3 grunts" % len(enemies))
    for enemy in enemies:
        cell = expected[int(enemy["y"])][int(enemy["x"])]
        if enemy["type"] != 0 or enemy["hp"] != 2 or cell != "0":
            problems.append("enemy %r is not a 2 hp grunt on a floor cell (cell %r)"
                            % (enemy, cell))
    return problems, ["start (%s, %s) facing (%d, %d), read from the file"
                      % (start_x, start_y, face_x, face_y)]


def check_fields(obs):
    problems, enemy_rows = [], 0
    for number, one in enumerate(obs, 1):
        for message in validate_obs(one):
            problems.append("observation %d: %s" % (number, message))
        if isinstance(one, dict) and isinstance(one.get("enemies"), list):
            enemy_rows += len(one["enemies"])
    if not obs:
        problems.append("no observation")
    if enemy_rows == 0:
        problems.append("no enemy was ever printed, so the enemy fields went unchecked")
    return problems, ["%d observations, %d enemy rows checked" % (len(obs), enemy_rows)]


def check_rate(obs):
    if len(obs) < 2:
        return ["fewer than 2 observations"], []
    span = obs[-1]["t"] - obs[0]["t"]
    rate = (len(obs) - 1) / span if span > 0 else 0.0
    problems = []
    if span < 8.0:
        problems.append("only %.1f s of game time in a 10 s run" % span)
    if rate < 40.0:
        problems.append("%.1f observations per second of t, expected at least 40" % rate)
    return problems, ["%.1f observations per second of t, over %.1f s" % (rate, span)]


def check_keeps_up(obs, run):
    problems = []
    if obs and obs[0]["frame"] != 1:
        problems.append("the first frame is %r, expected 1" % obs[0]["frame"])
    for before, after in zip(obs, obs[1:]):
        if after["frame"] != before["frame"] + 1:
            problems.append("frame %d is followed by frame %d" % (before["frame"], after["frame"]))
            break
    if any(one["drops"] != 0 for one in obs):
        problems.append("drops is not 0 with a reader that keeps up")
    if not run.alive_at_end:
        problems.append("the game was not running at the end of the run")
    return problems, []


def check_stalled(records, bad, run):
    obs = records[1:]
    problems = list(bad)
    if len(obs) < 2:
        return problems + ["fewer than 2 observations"], []
    missing = obs[-1]["frame"] - obs[0]["frame"] + 1 - len(obs)
    if obs[-1]["drops"] == 0:
        problems.append("no line was dropped: the pipe never filled, so the drop "
                        "path was not exercised")
    if obs[-1]["drops"] != missing:
        problems.append("drops says %d but %d frame numbers are missing"
                        % (obs[-1]["drops"], missing))
    if not run.alive_at_end:
        problems.append("the game was not running at the end of the stall")
    return problems, ["%d lines kept, %d dropped, game time reached %.1f s"
                      % (len(obs), obs[-1]["drops"], obs[-1]["t"])]


def check_stderr(*runs):
    problems = ["stderr was not empty: %r" % run.stderr[:200] for run in runs if run.stderr]
    return problems, []


# ------------------------------------------------------- the commands (T3c): sessions
# A session starts a game, sends commands in phases and keeps the observations of
# each phase. Speeds are measured in the game's own time, so they do not depend on
# how exactly this script sleeps.

class Session:
    def __init__(self, phases=None, run=None, error=None):
        self.phases = phases or {}
        self.run = run
        self.error = error


def phase(game, phases, name, steps):
    """Run steps, a list of (text to send, seconds to read), and keep the observations."""
    mark = len(game.lines)
    for text, seconds in steps:
        if text:
            game.send(text)
        game.read(seconds)
    phases[name] = observations(game.lines[mark:])


def run_session(script, map_path=MAP):
    """Start the game, run script(game, phases), and always stop the game."""
    game = Game(map_path)
    phases = {}
    try:
        if not game.start():
            raise RuntimeError("the game printed no init line and observation in 15 s")
        script(game, phases)
        return Session(phases, game.finish())
    except Exception as error:  # a broken session is a FAIL for its checks, not a crash
        game.finish()
        return Session(error="%s: %s" % (type(error).__name__, error))


# Lines the game must ignore, each worth one warning on stderr. The last has 8 flags.
GARBAGE = ["hello\n", "C 1 0 0\n", "C 2 0 0 0 0 0 0\n", "c 1 0 0 0 0 0 0\n",
           "C 1 0 0 0 0 0 0 0\n", "C  1 0 0 0 0 0 0\n", "x" * 400 + "\n"]


def script_moves(game, phases):
    phase(game, phases, "garbage", [(line, 0.05) for line in GARBAGE] + [("", 0.3)])
    # The first command arrives in two writes: a line cut in half must still work.
    phase(game, phases, "forward", [("C 1 0 0 ", 0.15), ("0 0 0 0\n", 1.0), (STOP, 0.3)])
    phase(game, phases, "back", [("C 0 1 0 0 0 0 0\n", 0.3), (STOP, 0.2)])
    phase(game, phases, "strafe_left", [("C 0 0 1 0 0 0 0\n", 0.3), (STOP, 0.2)])
    phase(game, phases, "strafe_right", [("C 0 0 0 1 0 0 0\n", 0.3), (STOP, 0.2)])


def script_turns(game, phases):
    phase(game, phases, "turn_left", [("C 0 0 0 0 1 0 0\n", 1.0), (STOP, 0.3)])
    phase(game, phases, "turn_right", [("C 0 0 0 0 0 1 0\n", 0.5), (STOP, 0.3)])


def script_fire(game, phases):
    # Read 0.2 s first, so the weapon is seen ready before the shot: without it the
    # first observation read could already be one taken after the shot.
    phase(game, phases, "pulse", [("", 0.2), ("C 0 0 0 0 0 0 1\n", 0.1), (STOP, 1.0)])
    phase(game, phases, "held", [("C 0 0 0 0 0 0 1\n", 1.5), (STOP, 0.8)])


def script_idle(game, phases):
    for number in (1, 2, 3):
        phase(game, phases, "idle%d" % number, [("", 3.0)])


def run_exit(how):
    """Start the game, stop it with "Q" or by closing stdin, and see how it exits."""
    game = Game()
    try:
        if not game.start():
            raise RuntimeError("the game printed no init line and observation in 15 s")
        began = time.monotonic()
        if how == "Q":
            game.send("Q\n")
        else:
            game.proc.stdin.close()
        try:
            code = game.proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            code = None
        return code, time.monotonic() - began, None
    except Exception as error:
        return None, 0.0, "%s: %s" % (type(error).__name__, error)
    finally:
        game.finish()


def run_on_terminal(seconds):
    """Run the game with a terminal (a pty) as stdin, stdout and stderr, as when someone
    types the command. Returns how many observation lines it printed and whether it was
    still running. A game that read the terminal would wait for a key and print nothing."""
    pid, master = pty.fork()
    if pid == 0:
        try:
            os.chdir(ROOT)
            os.execv(BINARY, [BINARY, MAP, str(SEED)])
        finally:
            os._exit(127)
    seen, deadline = 0, time.monotonic() + seconds
    try:
        while time.monotonic() < deadline:
            ready, _, _ = select.select([master], [], [], 0.5)
            if not ready:
                continue
            try:
                chunk = os.read(master, 65536)
            except OSError:
                break  # the game exited and closed the terminal
            if not chunk:
                break
            seen += chunk.count(b'"type":"obs"')
        alive = os.waitpid(pid, os.WNOHANG) == (0, 0)
    finally:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        os.waitpid(pid, 0)
        os.close(master)
    return seen, alive


def pose(one):
    return one["player"]["x"], one["player"]["y"]


def heading(one):
    return math.atan2(one["player"]["dy"], one["player"]["dx"])


def moved(before, after):
    return math.dist(pose(before), pose(after)) > 0.0005


def wrap(angle):
    """An angle difference brought into (-pi, pi]."""
    return (angle + math.pi) % (2 * math.pi) - math.pi


def turned(before, after):
    return abs(wrap(heading(after) - heading(before))) > 0.003


def active_span(obs, changed):
    """The first and last index between which something changed, or None."""
    steps = [k for k in range(len(obs) - 1) if changed(obs[k], obs[k + 1])]
    return (steps[0], steps[-1] + 1) if steps else None


def check_garbage(session):
    if session.error:
        return [session.error], []
    obs = session.phases["garbage"]
    problems = []
    if len(obs) < 5:
        problems.append("only %d observations while the garbage was sent" % len(obs))
    elif active_span(obs, moved) or active_span(obs, turned):
        problems.append("the player moved or turned: a malformed line was applied")
    warnings = session.run.stderr.count("ignored")
    if warnings != len(GARBAGE):
        problems.append("%d warnings on stderr for %d malformed lines (stderr: %r)"
                        % (warnings, len(GARBAGE), session.run.stderr[:160]))
    return problems, ["%d malformed lines sent, none applied" % len(GARBAGE)]


def check_move(session, name, direction, distance=None, expected_speed=MOVE_SPEED):
    if session.error:
        return [session.error], []
    obs = session.phases[name]
    span = active_span(obs, moved)
    if span is None:
        return ["the player did not move"], []
    first, last = obs[span[0]], obs[span[1]]
    dx, dy = pose(last)[0] - pose(first)[0], pose(last)[1] - pose(first)[1]
    length = math.hypot(dx, dy)
    seconds = last["t"] - first["t"]
    speed = length / seconds
    problems = []
    if (dx * direction[0] + dy * direction[1]) / length < 0.99:
        problems.append("moved by (%.2f, %.2f), expected along %s" % (dx, dy, direction))
    if abs(speed - expected_speed) > 0.1 * expected_speed:
        problems.append("%.2f cells/s, expected %.2f +-10%%" % (speed, expected_speed))
    if distance is not None and abs(length - distance) > 0.1 * distance:
        problems.append("%.2f cells after about 1 s, expected %.1f +-10%%" % (length, distance))
    if any(moved(a, b) for a, b in zip(obs[-3:], obs[-2:])):
        problems.append("still moving at the end: the stop command did not stop it")
    return problems, ["%.2f cells in %.2f s of game time = %.2f cells/s"
                      % (length, seconds, speed)]


def check_turn(session, name, sign, angle=None):
    if session.error:
        return [session.error], []
    obs = session.phases[name]
    span = active_span(obs, turned)
    if span is None:
        return ["the player did not turn"], []
    total = sum(wrap(heading(obs[k + 1]) - heading(obs[k])) for k in range(*span))
    seconds = obs[span[1]]["t"] - obs[span[0]]["t"]
    rate = total / seconds
    problems = []
    if sign * total <= 0:
        problems.append("turned by %.2f rad, the wrong way" % total)
    if abs(abs(rate) - TURN_SPEED) > 0.1 * TURN_SPEED:
        problems.append("%.2f rad/s, expected %.1f +-10%%" % (abs(rate), TURN_SPEED))
    if angle is not None and abs(abs(total) - angle) > 0.1 * angle:
        problems.append("%.2f rad after about 1 s, expected %.1f +-10%%" % (abs(total), angle))
    if any(turned(a, b) for a, b in zip(obs[-3:], obs[-2:])):
        problems.append("still turning at the end: the stop command did not stop it")
    return problems, ["%.2f rad in %.2f s of game time = %.2f rad/s" % (total, seconds, rate)]


def check_pulse(session):
    if session.error:
        return [session.error], []
    obs = session.phases["pulse"]
    ready = [one["weapon_ready"] for one in obs]
    if 0 not in ready:
        return ["weapon_ready never dropped to 0: no shot was fired"], []
    shot = ready.index(0)
    if 1 not in ready[shot:]:
        return ["weapon_ready never came back to 1"], []
    back = shot + ready[shot:].index(1)
    cooldown = obs[back]["t"] - obs[shot]["t"]
    problems = []
    if shot == 0:
        problems.append("the weapon was not ready before the shot")
    if abs(cooldown - FIRE_COOLDOWN) > 0.1 * FIRE_COOLDOWN:
        problems.append("ready again after %.2f s, expected %.1f +-10%%"
                        % (cooldown, FIRE_COOLDOWN))
    if 0 in ready[back:]:
        problems.append("a second shot was fired after the pulse was released")
    return problems, ["weapon_ready was 0 for %.2f s" % cooldown]


def check_held(session):
    if session.error:
        return [session.error], []
    obs = session.phases["held"]
    ready = [one["weapon_ready"] for one in obs]
    if 0 not in ready:
        return ["weapon_ready never dropped to 0: no shot was fired"], []
    shot = ready.index(0)
    window = [one["weapon_ready"] for one in obs[shot:]
              if one["t"] - obs[shot]["t"] <= 1.3]
    problems = []
    if 1 in window:
        problems.append("weapon_ready came back to 1 while fire was held")
    if ready[-1] != 1:
        problems.append("weapon_ready did not come back to 1 after fire was released")
    return problems, ["weapon_ready stayed 0 for %d observations, then came back" % len(window)]


def check_exit(result):
    code, seconds, error = result
    if error:
        return [error], []
    problems = []
    if code is None:
        problems.append("the game was still running 3 s later")
    elif code != 0:
        problems.append("exit code %d, expected 0" % code)
    elif seconds > 1.0:
        problems.append("exited after %.2f s, expected under 1 s" % seconds)
    return problems, ["exit code %s after %.2f s" % (code, seconds)]


def check_terminal(result):
    seen, alive = result
    problems = []
    if seen < 100:
        problems.append("only %d observations in 4 s: the game waited for the terminal" % seen)
    if not alive:
        problems.append("the game exited on its own")
    return problems, ["%d observations in 4 s with a terminal as stdin and stdout" % seen]


def check_idle_rate(session):
    """The best of three stretches must be within 10% of the baseline. A shared
    machine only ever slows a stretch down (a stall of the VM costs frames), so the
    best one is what the build can do; a real cost in the bridge would lower all
    three."""
    if session.error:
        return [session.error], []
    rates = []
    for name in ("idle1", "idle2", "idle3"):
        obs = session.phases[name]
        if len(obs) < 2 or obs[-1]["t"] <= obs[0]["t"]:
            return ["fewer than 2 observations in %s" % name], []
        rates.append((len(obs) - 1) / (obs[-1]["t"] - obs[0]["t"]))
    best = max(rates)
    problems = []
    if abs(best - FPS_ON_MINIMAL) > 0.1 * FPS_ON_MINIMAL:
        problems.append("the best of three is %.1f observations per second of t, "
                        "expected %.0f +-10%%" % (best, FPS_ON_MINIMAL))
    return problems, ["observations per second of t on minimal, three stretches of "
                      "3 s: %s" % ", ".join("%.1f" % rate for rate in rates)]


# ------------------------------------------------------------------------- driver

def fatal(message):
    print("check_bridge.py: " + message, file=sys.stderr)
    sys.exit(2)


def main():
    if "DISPLAY" not in os.environ:
        fatal("DISPLAY is not set; the game needs a screen. Start Xvfb and "
              "export DISPLAY=:99")
    if not os.access(BINARY, os.X_OK):
        fatal("%s is missing; build it first: make -C agent" % BINARY)
    expected = read_map_file(os.path.join(ROOT, MAP))
    print("check_bridge.py: observations on %s, seed %d (10 s, then 8 s with a stalled "
          "reader), then commands in 6 short runs" % (MAP, SEED))
    run_a = run_game(10)
    run_b = run_game(8, stall=5)
    records_a, bad_a = parse(run_a)
    records_b, bad_b = parse(run_b)
    obs_a = records_a[1:]
    moves = run_session(script_moves)
    turns = run_session(script_turns)
    fire = run_session(script_fire)
    idle = run_session(script_idle, MINIMAL_MAP)
    failed = []

    def section(name, result):
        problems, notes = result
        print("%s %s" % ("FAIL" if problems else "PASS", name))
        for line in notes + problems[:5]:
            print("     " + line)
        if problems:
            failed.append(name)

    def guarded(name, check, *args):
        try:
            section(name, check(*args))
        except Exception as error:  # a broken check must fail loudly, not crash the run
            section(name, ([("%s: %s" % (type(error).__name__, error))], []))

    print("--- what the game prints")
    section("lines are JSON", (bad_a, ["%d lines" % len(run_a.lines)]))
    guarded("init line matches the map file", check_init, records_a, expected)
    guarded("first observation matches the start", check_first_obs, obs_a, expected)
    guarded("every observation has exactly the contract's fields", check_fields, obs_a)
    guarded("at least 40 observations per second of t", check_rate, obs_a)
    guarded("drops == 0 and no frame missing with a reader that keeps up",
            check_keeps_up, obs_a, run_a)
    guarded("a stalled reader never blocks the game nor cuts a line",
            check_stalled, records_b, bad_b, run_b)
    guarded("stderr is empty", check_stderr, run_a, run_b)

    print("--- what the game obeys")
    guarded("malformed lines are ignored and reported", check_garbage, moves)
    guarded("C 1 0 0 0 0 0 0 (in two writes): forward, 1.2 cells/s",
            check_move, moves, "forward", (0, -1), 1.2)
    guarded("C 0 1 0 0 0 0 0: back, 1.2 cells/s", check_move, moves, "back", (0, 1))
    guarded("C 0 0 1 0 0 0 0: strafe left, 0.79 cells/s (1.2 x the 0.66 plane)",
            check_move, moves, "strafe_left", (-1, 0), None, STRAFE_SPEED)
    guarded("C 0 0 0 1 0 0 0: strafe right, 0.79 cells/s (1.2 x the 0.66 plane)",
            check_move, moves, "strafe_right", (1, 0), None, STRAFE_SPEED)
    guarded("C 0 0 0 0 1 0 0: turn left, 1.8 rad/s", check_turn, turns, "turn_left", -1, 1.8)
    guarded("C 0 0 0 0 0 1 0: turn right, 1.8 rad/s", check_turn, turns, "turn_right", 1)
    guarded("fire pulse: weapon_ready is 0 for 0.6 s", check_pulse, fire)
    guarded("held fire keeps weapon_ready at 0 until released", check_held, fire)
    guarded("Q exits with code 0 within 1 s", check_exit, run_exit("Q"))
    guarded("closing stdin exits with code 0 within 1 s", check_exit, run_exit("EOF"))
    guarded("a terminal as stdin and stdout is left alone: the game keeps running",
            check_terminal, run_on_terminal(4))
    guarded("no commands: 75 observations per second on minimal.cub (+-10%, best of 3)",
            check_idle_rate, idle)

    print()
    if not failed:
        print("ALL PASSED")
        return 0
    print("FAILED: %d check(s)" % len(failed))
    return 1


if __name__ == "__main__":
    sys.exit(main())
