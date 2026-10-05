#!/usr/bin/env python3
"""Checks of the C bridge in sources/jev/ (spec 002): what cub3D_agent prints.

Standard library only, so it runs where the game runs: inside the kube-dev
container (Python 3.10, no uv) and on native Linux alike.

    docker exec -e DISPLAY=:99 -w /kube kube-dev python3 agent/check_bridge.py   # Mac
    DISPLAY=:99 python3 agent/check_bridge.py                                    # Linux

It starts ./agent/cub3D_agent itself, with stdin open and silent (EOF would make
the game quit), and reads its stdout as it comes. It prints PASS or FAIL per
check and exits 1 if any failed. Build the binary first: make -C agent
"""
import json
import os
import select
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BINARY = os.path.join(ROOT, "agent", "cub3D_agent")
MAP = "maps/bonus/subject_map.cub"
SEED = 1

# The contract of plan.md, "Contracts / Game -> agent": fields, in this order.
INIT_KEYS = ["type", "map", "width", "height", "seed"]
OBS_KEYS = ["type", "frame", "t", "dt", "state", "wave", "hp", "weapon_ready",
            "player", "drops", "enemies"]
PLAYER_KEYS = ["x", "y", "dx", "dy"]
ENEMY_KEYS = ["x", "y", "type", "hp", "ai", "los"]
FACING = {"N": (0, -1), "S": (0, 1), "E": (1, 0), "W": (-1, 0)}
TERRAIN = str.maketrans("NSEW ", "00001")  # start cells become floor, spaces walls
MAP_IDENTIFIERS = ("NO", "SO", "WE", "EA", "F", "C")


class Run:
    """What one run of the game printed."""

    def __init__(self, lines, stderr, alive_at_end):
        self.lines = lines
        self.stderr = stderr
        self.alive_at_end = alive_at_end


def run_game(seconds, stall=0.0):
    """Run cub3D_agent for `seconds`. The first `stall` seconds nothing is read."""
    stderr = tempfile.TemporaryFile()
    proc = subprocess.Popen([BINARY, MAP, str(SEED)], cwd=ROOT,
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=stderr)
    fd = proc.stdout.fileno()
    lines, buffer = [], b""
    start = time.monotonic()
    time.sleep(stall)
    try:
        while time.monotonic() - start < seconds:
            ready, _, _ = select.select([fd], [], [], 0.5)
            if not ready:
                continue
            chunk = os.read(fd, 65536)
            if not chunk:
                break  # EOF: the game exited
            buffer += chunk
            *whole, buffer = buffer.split(b"\n")
            lines.extend(whole)
        alive = proc.poll() is None
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        proc.stdout.close()
        proc.stdin.close()
    stderr.seek(0)
    return Run(lines, stderr.read().decode(errors="replace"), alive)


def parse(run):
    """The JSON records of a run, and a message for every line that is not JSON."""
    records, bad = [], []
    for number, raw in enumerate(run.lines, 1):
        try:
            records.append(json.loads(raw))
        except ValueError:
            bad.append("line %d is not JSON: %r" % (number, raw[:60]))
    return records, bad


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


# --------------------------------------------------------------------- the checks
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
    print("check_bridge.py: %s, seed %d: 10 s with a reader that keeps up, then 8 s "
          "with one that stalls for 5 s" % (MAP, SEED))
    run_a = run_game(10)
    run_b = run_game(8, stall=5)
    records_a, bad_a = parse(run_a)
    records_b, bad_b = parse(run_b)
    obs_a = records_a[1:]
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

    print()
    if not failed:
        print("ALL PASSED")
        return 0
    print("FAILED: %d check(s)" % len(failed))
    return 1


if __name__ == "__main__":
    sys.exit(main())
