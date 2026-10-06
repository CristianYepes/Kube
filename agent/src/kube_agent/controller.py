"""The code that plays: aim, fire and move, whatever tactic was chosen.

Jev (or the scripted rules) picks only the tactic. This module turns tactic + observation + map
into the `C` line for the game, on every observation. The numbers are those of
specs/002-jev-agent/plan.md ("Controller (exact)"); the game's own hitscan is in combat.c.
"""

import math
from collections import deque

from kube_agent.features import open_directions, relative, walkable

TACTICS = ("ENGAGE", "KITE", "RETREAT", "SEARCH")

DEAD_ZONE = 0.25  # cells off the aim line, like the hitscan's perp: inside it the player stops turning
FIRE_MARGIN = 0.45  # cells off the aim line; the game hits within 0.5
FIRE_RANGE = 10.0  # cells; the game's hitscan reaches 10
MOVE_THRESHOLD = 0.3  # of the unit vector, to press a movement key
RETREAT_DEPTH = 8  # steps of the breadth-first search
KITE_PROBE = 0.6  # cells behind the player that must be walkable to back away
STUCK_DISTANCE = 0.05  # cells moved in STUCK_WINDOW below which the player is stuck
STUCK_WINDOW = 0.5  # seconds

NO_KEYS = "C 0 0 0 0 0 0 0"  # the game starts with no key held
STILL = (0.0, 0.0)
NEIGHBOURS = ((0, -1), (1, 0), (0, 1), (-1, 0))  # up, right, down, left, as (column, row)


def pick_target(player: dict, enemies: list[dict]) -> dict | None:
    """The nearest enemy with line of sight, or the nearest enemy if none has it."""
    seen = [enemy for enemy in enemies if enemy["los"] == 1]
    return _nearest(player, seen or enemies)


def turn_toward(player: dict, point: dict) -> tuple[bool, bool]:
    """(turn_left, turn_right) to face `point`, doing nothing inside the dead zone ahead.

    The zone is measured in cells off the aim line, like the hitscan, so it narrows with
    distance. An angular zone would stop the aim too far off the line to hit a far target.
    """
    ahead, right = relative(player, point)
    if ahead > 0 and abs(right) < DEAD_ZONE:
        return False, False
    return (False, True) if right >= 0 else (True, False)


def should_fire(player: dict, target: dict | None, weapon_ready: int) -> bool:
    """The same conditions as the game's hitscan, with a margin: the shot has to land."""
    if target is None or weapon_ready != 1 or target["los"] != 1:
        return False
    ahead, right = relative(player, target)
    return 0 < ahead < FIRE_RANGE and abs(right) < FIRE_MARGIN


def movement_flags(player: dict, w: tuple[float, float]) -> tuple[bool, bool, bool, bool]:
    """(forward, back, strafe_left, strafe_right) to go along the world vector `w`."""
    length = math.hypot(*w)
    if length == 0:
        return False, False, False, False
    unit_x, unit_y = w[0] / length, w[1] / length
    along = unit_x * player["dx"] + unit_y * player["dy"]
    across = unit_x * -player["dy"] + unit_y * player["dx"]  # the unit vector to the right is (-dy, dx)
    return along > MOVE_THRESHOLD, along < -MOVE_THRESHOLD, across < -MOVE_THRESHOLD, across > MOVE_THRESHOLD


def reachable(game_map: list[str], start: tuple[int, int], max_depth: int | None = None) -> dict:
    """Breadth-first search over walkable cells with 4 neighbours; cells are (column, row).

    Returns {cell: (steps, first_step)}, where first_step is the cell to enter first on a
    shortest path (None for the start itself).
    """
    found = {start: (0, None)}
    queue = deque([start])
    while queue:
        cell = queue.popleft()
        steps, first = found[cell]
        if steps == max_depth:
            continue
        for d_col, d_row in NEIGHBOURS:
            neighbour = (cell[0] + d_col, cell[1] + d_row)
            if neighbour not in found and walkable(game_map, neighbour[0] + 0.5, neighbour[1] + 0.5):
                found[neighbour] = (steps + 1, neighbour if first is None else first)
                queue.append(neighbour)
    return found


class PositionTrail:
    """Where the player was over the last half second, to tell whether it is stuck."""

    def __init__(self) -> None:
        self._samples: deque[tuple[float, float, float]] = deque()  # (t, x, y), oldest first

    def add(self, t: float, x: float, y: float) -> None:
        self._samples.append((t, x, y))
        # Keep the newest sample that is a full window old, and every sample after it.
        while len(self._samples) > 1 and self._samples[1][0] <= t - STUCK_WINDOW:
            self._samples.popleft()

    def moved(self, t: float, x: float, y: float) -> float | None:
        """Distance from the newest sample at least one window old, or None if there is none."""
        reference = None
        for sample_t, sample_x, sample_y in self._samples:
            if sample_t > t - STUCK_WINDOW:
                break
            reference = (sample_x, sample_y)
        return None if reference is None else math.hypot(x - reference[0], y - reference[1])


class Controller:
    """One per episode: it remembers the map, the last line sent and the player's recent path."""

    def __init__(self, game_map: list[str]) -> None:
        self._map = game_map
        self._trail = PositionTrail()
        self._unstick_side: str | None = None
        self._unstick_until = -math.inf
        self._last_sent = NO_KEYS

    def command(self, obs: dict, tactic: str) -> str | None:
        """The line to send now, or None when it is the one already in force."""
        line = self.decide(obs, tactic)
        if line == self._last_sent:
            return None
        self._last_sent = line
        return line

    def decide(self, obs: dict, tactic: str) -> str:
        """The `C` line this observation calls for, whether or not it was sent before."""
        if tactic not in TACTICS:
            raise ValueError(f"unknown tactic {tactic!r}: expected one of {TACTICS}")
        player, enemies = obs["player"], obs["enemies"]
        target = pick_target(player, enemies)
        w, aim = self._plan(tactic, player, enemies, target)

        turn_left, turn_right = turn_toward(player, aim) if aim else (False, False)
        forward, back, strafe_left, strafe_right = movement_flags(player, w)
        side = self._unstick(obs, wants_to_move=any(w))
        if side:  # the unsticking strafe replaces any strafe the path asked for
            strafe_left, strafe_right = side == "left", side == "right"
        fire = should_fire(player, target, obs["weapon_ready"])

        flags = (forward, back, strafe_left, strafe_right, turn_left, turn_right, fire)
        return "C " + " ".join(str(int(flag)) for flag in flags)

    def _plan(self, tactic, player, enemies, target):
        """The world vector to move along and the point to aim at (None for no aim)."""
        if tactic == "ENGAGE":
            return STILL, target
        if tactic == "KITE":
            return self._kite_vector(player, enemies, target), target
        if tactic == "RETREAT":
            return self._retreat_vector(player, enemies), target
        return self._search(player, enemies, target)

    def _kite_vector(self, player, enemies, target):
        if target is None:
            return STILL
        away_x, away_y = player["x"] - target["x"], player["y"] - target["y"]
        length = math.hypot(away_x, away_y)
        if length == 0:
            return STILL
        away = (away_x / length, away_y / length)
        if walkable(self._map, player["x"] + KITE_PROBE * away[0], player["y"] + KITE_PROBE * away[1]):
            return away
        return self._retreat_vector(player, enemies)

    def _retreat_vector(self, player, enemies):
        """Toward the reachable cell, within RETREAT_DEPTH steps, farthest from every enemy."""
        found = reachable(self._map, _cell(player), RETREAT_DEPTH)

        def score(item):
            cell, (steps, _) = item
            centre = _centre(cell)
            nearest_enemy = min((_distance(centre, enemy) for enemy in enemies), default=math.inf)
            return nearest_enemy, -steps  # on a tie, the cell with fewer steps

        _, (_, first_step) = max(found.items(), key=score)
        return STILL if first_step is None else _toward(player, _centre(first_step))

    def _search(self, player, enemies, target):
        """Walk toward the nearest enemy, aiming at the next cell of the path, not at the enemy."""
        goal = _nearest(player, enemies)
        if goal is None:
            return STILL, None
        entry = reachable(self._map, _cell(player)).get(_cell(goal))
        if entry is None or entry[1] is None:  # no way there, or the enemy is in the player's cell
            return STILL, target
        step = _centre(entry[1])
        return _toward(player, step), step

    def _unstick(self, obs, wants_to_move):
        """'left' or 'right' while a strafe is needed to get unstuck, else None."""
        t, player = obs["t"], obs["player"]
        self._trail.add(t, player["x"], player["y"])
        if not wants_to_move:
            return None
        if t < self._unstick_until:
            return self._unstick_side
        moved = self._trail.moved(t, player["x"], player["y"])
        if moved is None or moved >= STUCK_DISTANCE:
            return None
        ways = open_directions(player, self._map)
        side = "right" if "right" in ways else "left" if "left" in ways else None
        if side:
            self._unstick_side, self._unstick_until = side, t + STUCK_WINDOW
        return side


def _distance(a: dict, b: dict) -> float:
    return math.hypot(a["x"] - b["x"], a["y"] - b["y"])


def _nearest(player: dict, points: list[dict]) -> dict | None:
    return min(points, key=lambda point: _distance(player, point), default=None)


def _cell(point: dict) -> tuple[int, int]:
    return math.floor(point["x"]), math.floor(point["y"])


def _centre(cell: tuple[int, int]) -> dict:
    return {"x": cell[0] + 0.5, "y": cell[1] + 0.5}


def _toward(player: dict, point: dict) -> tuple[float, float]:
    return point["x"] - player["x"], point["y"] - player["y"]
