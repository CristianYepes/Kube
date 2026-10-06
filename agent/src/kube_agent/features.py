"""Observations to the semantic state: what Jev reads and what the scripted policy decides on.

Pure functions, plus HpHistory for the one feature that needs the past. The values are those of
specs/002-jev-agent/plan.md ("Conventions", "Semantic features"). Nothing in the state has a
decimal point: Jev compares numbers badly, so the numbers become words here.
"""

import math
from collections import deque

TOUCHING_BELOW = 1.0
CLOSE_BELOW = 2.5
MEDIUM_BELOW = 6.0
HIGH_HEALTH_FROM = 60
MEDIUM_HEALTH_FROM = 30
FOV_HALF_ANGLE = 0.583  # atan(0.66): the camera plane's length is 0.66
HIT_WINDOW = 1.0  # seconds: being hit means less hp than this long ago
WAVES = 3
BOSS_TYPE = 2
ENEMY_KINDS = {0: ("grunt", 2), 1: ("runner", 1), 2: ("boss", 8)}  # type: (name, hp at spawn)
NOT_WALKABLE = "1D"  # walls and closed doors; sprites (2) and open doors (O) can be walked on


def relative(player: dict, enemy: dict) -> tuple[float, float]:
    """(ahead, right) of the enemy seen from the player: positive is in front and to the right.

    y grows downward and `dir` rotates clockwise, so facing east (1, 0) the right is south.
    """
    vx = enemy["x"] - player["x"]
    vy = enemy["y"] - player["y"]
    return player["dx"] * vx + player["dy"] * vy, player["dx"] * vy - player["dy"] * vx


def distance_band(distance: float) -> str:
    if distance < TOUCHING_BELOW:
        return "touching"
    if distance < CLOSE_BELOW:
        return "close"
    if distance < MEDIUM_BELOW:
        return "medium"
    return "far"


def health_band(hp: int) -> str:
    if hp >= HIGH_HEALTH_FROM:
        return "high"
    if hp >= MEDIUM_HEALTH_FROM:
        return "medium"
    return "low"


def direction_name(bearing: float) -> str:
    """One of 8 sectors of 45 degrees, centred ahead. The bearing is 0 ahead, positive to the right."""
    side = "right" if bearing > 0 else "left"
    angle = abs(bearing)
    if angle < math.radians(22.5):
        return "ahead"
    if angle < math.radians(67.5):
        return f"ahead-{side}"
    if angle < math.radians(112.5):
        return side
    if angle < math.radians(157.5):
        return f"behind-{side}"
    return "behind"


def in_view(enemy: dict, bearing: float) -> bool:
    return enemy["los"] == 1 and abs(bearing) <= FOV_HALF_ANGLE


def _walkable(game_map: list[str], x: float, y: float) -> bool:
    row, col = math.floor(y), math.floor(x)
    # The bounds are explicit: a negative index would wrap around to the far side of the map.
    return 0 <= row < len(game_map) and 0 <= col < len(game_map[row]) and game_map[row][col] not in NOT_WALKABLE


def open_directions(player: dict, game_map: list[str]) -> list[str]:
    """The ways with a walkable cell 1.0 away, in the order ahead, back, right, left."""
    dx, dy = player["dx"], player["dy"]
    probes = {"ahead": (dx, dy), "back": (-dx, -dy), "right": (-dy, dx), "left": (dy, -dx)}
    return [
        name for name, (vx, vy) in probes.items()
        if _walkable(game_map, player["x"] + vx, player["y"] + vy)
    ]


class HpHistory:
    """The player's hp over the last second or so. Call add() on every observation."""

    def __init__(self) -> None:
        self._samples: deque[tuple[float, int]] = deque()  # (t, hp), oldest first

    def add(self, obs: dict) -> None:
        self._samples.append((obs["t"], obs["hp"]))
        # Keep the newest sample that is a full window old, and every sample after it.
        while len(self._samples) > 1 and self._samples[1][0] <= obs["t"] - HIT_WINDOW:
            self._samples.popleft()

    def hp_a_window_ago(self, t: float) -> int | None:
        """The hp of the newest sample at least one window older than t, or None if none is."""
        reference = None
        for sample_t, hp in self._samples:
            if sample_t > t - HIT_WINDOW:
                break
            reference = hp
        return reference


def semantic_state(obs: dict, game_map: list[str], history: HpHistory, tactic: str) -> dict:
    player = obs["player"]
    seen = []  # (distance, bearing, enemy)
    for enemy in obs["enemies"]:
        if enemy["type"] not in ENEMY_KINDS:
            raise ValueError(f"unknown enemy type {enemy['type']} in an observation: {enemy}")
        ahead, right = relative(player, enemy)
        seen.append((math.hypot(ahead, right), math.atan2(right, ahead), enemy))

    hp_before = history.hp_a_window_ago(obs["t"])
    ways = open_directions(player, game_map)
    return {
        "player": {
            "health": health_band(obs["hp"]),
            "weapon": "ready" if obs["weapon_ready"] == 1 else "reloading",
            "being_hit": hp_before is not None and obs["hp"] < hp_before,
        },
        "threats": {
            "remaining": len(seen),
            "in_view": sum(in_view(enemy, bearing) for _, bearing, enemy in seen),
            "nearest": _describe_nearest(seen),
            "close_count": sum(distance < CLOSE_BELOW for distance, _, _ in seen),
        },
        "space": {"open_directions": ways, "cornered": len(ways) <= 1},
        "progress": {
            "wave": f"{obs['wave']} of {WAVES}",
            "boss_present": any(enemy["type"] == BOSS_TYPE for _, _, enemy in seen),
        },
        "current_tactic": tactic,
    }


def _describe_nearest(seen: list[tuple[float, float, dict]]) -> dict | None:
    if not seen:
        return None
    distance, bearing, enemy = min(seen, key=lambda entry: entry[0])
    kind, spawn_hp = ENEMY_KINDS[enemy["type"]]
    return {
        "direction": direction_name(bearing),
        "distance": distance_band(distance),
        "kind": kind,
        "wounded": enemy["hp"] < spawn_hp,
    }
