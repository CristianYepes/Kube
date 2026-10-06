"""Hand-made observations shared by the tests. Coordinates: x grows east, y grows south."""

import math

ROOM = ["111111111111"] + ["100000000000"] * 10 + ["111111111111"]  # open inside, walls around


def player(x=5.5, y=5.5, dx=1.0, dy=0.0):
    return {"x": x, "y": y, "dx": dx, "dy": dy}


def enemy(x, y, type=0, hp=2, los=1):
    return {"x": x, "y": y, "type": type, "hp": hp, "ai": 1, "los": los}


def enemy_at(bearing_degrees, distance, **fields):
    """An enemy seen from the default player (5.5, 5.5), facing east, at that bearing."""
    angle = math.radians(bearing_degrees)
    return enemy(5.5 + distance * math.cos(angle), 5.5 + distance * math.sin(angle), **fields)


def enemy_ahead(ahead, right, **fields):
    """An enemy `ahead` cells in front of and `right` cells to the right of the default player.

    The default player faces east, so ahead is +x and right is +y (south).
    """
    return enemy(5.5 + ahead, 5.5 + right, **fields)


def make_obs(enemies=(), hp=100, weapon_ready=1, wave=1, t=0.0, **player_fields):
    return {
        "type": "obs", "frame": 1, "t": t, "dt": 0.01, "state": 0, "wave": wave, "hp": hp,
        "weapon_ready": weapon_ready, "player": player(**player_fields), "drops": 0,
        "enemies": list(enemies),
    }
