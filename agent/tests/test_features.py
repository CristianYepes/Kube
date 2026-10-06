import json
import math
import re
from pathlib import Path

import pytest

from kube_agent.features import (
    HpHistory,
    direction_name,
    distance_band,
    health_band,
    in_view,
    open_directions,
    relative,
    semantic_state,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"
ROOM = ["111111111111"] + ["100000000000"] * 10 + ["111111111111"]  # open inside, walls around


def player(x=5.5, y=5.5, dx=1.0, dy=0.0):
    return {"x": x, "y": y, "dx": dx, "dy": dy}


def enemy(x, y, type=0, hp=2, los=1):
    return {"x": x, "y": y, "type": type, "hp": hp, "ai": 1, "los": los}


def enemy_at(bearing_degrees, distance, **fields):
    """An enemy seen from the default player (5.5, 5.5), facing east, at that bearing."""
    angle = math.radians(bearing_degrees)
    return enemy(5.5 + distance * math.cos(angle), 5.5 + distance * math.sin(angle), **fields)


def make_obs(enemies=(), hp=100, weapon_ready=1, wave=1, t=0.0, **player_fields):
    return {
        "type": "obs", "frame": 1, "t": t, "dt": 0.01, "state": 0, "wave": wave, "hp": hp,
        "weapon_ready": weapon_ready, "player": player(**player_fields), "drops": 0,
        "enemies": list(enemies),
    }


def state_of(obs, game_map=ROOM, history=None, tactic="ENGAGE"):
    return semantic_state(obs, game_map, history or HpHistory(), tactic)


# --- the conventions of plan.md ---------------------------------------------------------------


def test_worked_example_an_enemy_one_row_up_is_on_the_left_when_facing_east():
    ahead, right = relative(player(5.5, 5.5, 1.0, 0.0), enemy(5.5, 4.5))

    assert (ahead, right) == (0.0, -1.0)  # right < 0 means left
    assert state_of(make_obs([enemy(5.5, 4.5)]))["threats"]["nearest"]["direction"] == "left"


def test_facing_north_the_right_is_east():
    ahead, right = relative(player(5.5, 5.5, 0.0, -1.0), enemy(6.5, 5.5))

    assert (ahead, right) == (0.0, 1.0)


# --- bands --------------------------------------------------------------------------------------


@pytest.mark.parametrize("distance, band", [
    (0.0, "touching"), (0.99, "touching"), (1.0, "close"), (2.49, "close"), (2.5, "medium"),
    (5.99, "medium"), (6.0, "far"), (30.0, "far"),
])
def test_distance_bands(distance, band):
    assert distance_band(distance) == band


@pytest.mark.parametrize("hp, band", [
    (100, "high"), (60, "high"), (59, "medium"), (30, "medium"), (29, "low"), (0, "low"),
])
def test_health_bands(hp, band):
    assert health_band(hp) == band


def test_the_distance_band_reaches_the_state_through_the_nearest_enemy():
    for x, band in [(6.49, "touching"), (6.5, "close"), (7.99, "close"), (8.0, "medium")]:
        assert state_of(make_obs([enemy(x, 5.5)]))["threats"]["nearest"]["distance"] == band


# --- direction ----------------------------------------------------------------------------------


@pytest.mark.parametrize("bearing, name", [
    (0, "ahead"), (45, "ahead-right"), (90, "right"), (135, "behind-right"), (180, "behind"),
    (-135, "behind-left"), (-90, "left"), (-45, "ahead-left"),
])
def test_all_eight_sectors(bearing, name):
    assert state_of(make_obs([enemy_at(bearing, 3.0)]))["threats"]["nearest"]["direction"] == name


@pytest.mark.parametrize("bearing, name", [
    (22.4, "ahead"), (22.6, "ahead-right"), (67.4, "ahead-right"), (67.6, "right"),
    (112.4, "right"), (112.6, "behind-right"), (157.4, "behind-right"), (157.6, "behind"),
    (-22.4, "ahead"), (-22.6, "ahead-left"), (-157.4, "behind-left"), (-157.6, "behind"),
])
def test_sector_edges(bearing, name):
    assert direction_name(math.radians(bearing)) == name


# --- in view ------------------------------------------------------------------------------------


@pytest.mark.parametrize("bearing, los, expected", [
    (0.58, 1, True), (0.59, 1, False), (-0.58, 1, True), (-0.59, 1, False), (0.0, 0, False),
])
def test_in_view_needs_line_of_sight_and_the_field_of_view(bearing, los, expected):
    candidate = enemy_at(math.degrees(bearing), 3.0, los=los)

    assert in_view(candidate, bearing) is expected


def test_threats_count_what_is_in_view_and_what_is_close():
    near_ahead = enemy_at(0, 2.0)
    far_left_in_view = enemy_at(-20, 8.0)
    behind = enemy_at(180, 1.5)
    hidden = enemy_at(0, 4.0, los=0)

    threats = state_of(make_obs([near_ahead, far_left_in_view, behind, hidden]))["threats"]

    assert threats["remaining"] == 4
    assert threats["in_view"] == 2  # behind is outside the field of view, hidden has no line of sight
    assert threats["close_count"] == 2  # under 2.5: near_ahead and behind


def test_close_count_stops_at_the_edge_of_the_close_band():
    assert state_of(make_obs([enemy_at(0, 2.49)]))["threats"]["close_count"] == 1
    assert state_of(make_obs([enemy_at(0, 2.5)]))["threats"]["close_count"] == 0


def test_nearest_is_none_with_no_enemies():
    threats = state_of(make_obs([]))["threats"]

    assert threats == {"remaining": 0, "in_view": 0, "nearest": None, "close_count": 0}


def test_nearest_describes_the_closest_enemy_with_its_kind_and_wounds():
    far_grunt = enemy_at(0, 5.0, type=0, hp=2)
    near_runner = enemy_at(90, 1.5, type=1, hp=1)
    wounded_boss = enemy_at(-90, 4.0, type=2, hp=5)

    assert state_of(make_obs([far_grunt, near_runner, wounded_boss]))["threats"]["nearest"] == {
        "direction": "right", "distance": "close", "kind": "runner", "wounded": False,
    }
    assert state_of(make_obs([wounded_boss]))["threats"]["nearest"]["wounded"] is True
    assert state_of(make_obs([wounded_boss]))["threats"]["nearest"]["kind"] == "boss"
    assert state_of(make_obs([enemy_at(0, 3.0, type=0, hp=1)]))["threats"]["nearest"]["wounded"] is True


def test_an_unknown_enemy_type_is_an_error_that_names_it():
    with pytest.raises(ValueError, match="enemy type 7"):
        state_of(make_obs([enemy_at(0, 3.0, type=7)]))


# --- space --------------------------------------------------------------------------------------


MAZE = [
    "11111",
    "10D01",
    "10001",
    "11111",
]


def test_open_directions_on_a_hand_made_map():
    # Facing north at (2.5, 2.5): ahead is the closed door D, back is a wall.
    assert open_directions(player(2.5, 2.5, 0.0, -1.0), MAZE) == ["right", "left"]


def test_an_open_door_is_walkable():
    opened = [row.replace("D", "O") for row in MAZE]

    assert open_directions(player(2.5, 2.5, 0.0, -1.0), opened) == ["ahead", "right", "left"]


@pytest.mark.parametrize("dx, dy, expected", [
    (0.0, -1.0, ["ahead", "right"]),  # north: the open cells are north and east
    (1.0, 0.0, ["ahead", "left"]),  # east: east is ahead, north is on the left
    (-1.0, 0.0, ["back", "right"]),  # west: east is behind, north is on the right
    (0.0, 1.0, ["back", "left"]),  # south: north is behind, east is on the left
])
def test_open_directions_follow_the_heading(dx, dy, expected):
    # Around (2.5, 2.5) only the cells north (row 1) and east (column 3) are floor.
    lopsided = ["11111", "11011", "11001", "11111"]

    assert open_directions(player(2.5, 2.5, dx, dy), lopsided) == expected


def test_cells_outside_the_map_are_closed_and_do_not_wrap_around():
    open_map = ["0000", "0000"]  # a wrapped negative index would find floor on the far side

    assert open_directions(player(0.5, 0.5, 0.0, -1.0), open_map) == ["back", "right"]


def test_cornered_means_at_most_one_way_out():
    corner = state_of(make_obs([], x=1.5, y=1.5, dx=0.0, dy=-1.0), game_map=MAZE)["space"]
    room = state_of(make_obs([]), game_map=ROOM)["space"]

    assert corner == {"open_directions": ["back"], "cornered": True}
    assert room["cornered"] is False
    assert room["open_directions"] == ["ahead", "back", "right", "left"]


# --- the rest of the state ----------------------------------------------------------------------


def test_player_progress_and_tactic_fields():
    state = state_of(
        make_obs([enemy_at(0, 3.0, type=2, hp=8)], hp=45, weapon_ready=0, wave=3), tactic="KITE")

    assert state["player"] == {"health": "medium", "weapon": "reloading", "being_hit": False}
    assert state["progress"] == {"wave": "3 of 3", "boss_present": True}
    assert state["current_tactic"] == "KITE"
    assert state_of(make_obs([], weapon_ready=1))["player"]["weapon"] == "ready"
    assert state_of(make_obs([enemy_at(0, 3.0)]))["progress"]["boss_present"] is False


# --- being hit ----------------------------------------------------------------------------------


def history_of(*samples):
    history = HpHistory()
    for t, hp in samples:
        history.add(make_obs(hp=hp, t=t))
    return history


def being_hit(history, t, hp):
    return state_of(make_obs(hp=hp, t=t), history=history)["player"]["being_hit"]


def test_hit_means_less_hp_than_one_second_ago():
    history = history_of((0.0, 100), (0.5, 100))

    assert being_hit(history, t=1.0, hp=90) is True  # the sample at t=0.0 is exactly 1.0 s old
    assert being_hit(history, t=1.0, hp=100) is False


def test_with_no_sample_a_full_second_old_nobody_is_being_hit():
    history = history_of((0.0, 100), (0.5, 100))

    assert being_hit(history, t=0.99, hp=10) is False


def test_it_compares_with_the_newest_sample_that_is_old_enough():
    history = history_of((0.0, 100), (0.4, 80), (0.8, 80), (1.2, 80))

    # At t=1.5 the reference is the sample at 0.4 (hp 80), not the one at 0.0 (hp 100).
    assert being_hit(history, t=1.5, hp=80) is False
    assert being_hit(history, t=1.5, hp=70) is True


def test_the_history_forgets_old_samples():
    history = HpHistory()
    for step in range(1000):
        history.add(make_obs(hp=100, t=step * 0.01))

    assert len(history._samples) < 130  # about 1 s of observations at 100 per second, plus slack


def test_hit_matches_a_brute_force_reading_of_the_recorded_game():
    obs = [json.loads(line) for line in (FIXTURES / "moves_seed7.jsonl").read_text().splitlines()][1:]
    history = HpHistory()
    hits = []
    for index, current in enumerate(obs):
        older = [o for o in obs[:index] if o["t"] <= current["t"] - 1.0]
        expected = bool(older) and current["hp"] < older[-1]["hp"]
        history.add(current)
        hits.append(state_of(current, history=history)["player"]["being_hit"])
        assert hits[-1] == expected, f"frame {current['frame']}"

    assert not any(hits[:100])
    assert any(hits)  # the recorded player does lose hp (100 to 90), so the check had work to do


# --- AC6: over every recorded observation -------------------------------------------------------


def floats_in(value):
    if isinstance(value, float):
        yield value
    elif isinstance(value, dict):
        for inner in value.values():
            yield from floats_in(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from floats_in(inner)


@pytest.mark.parametrize("fixture", ["idle_seed7.jsonl", "moves_seed7.jsonl"])
def test_ac6_every_recorded_state_is_small_and_has_no_float(fixture):
    rows = [json.loads(line) for line in (FIXTURES / fixture).read_text().splitlines()]
    game_map, observations = rows[0]["map"], rows[1:]
    history = HpHistory()
    longest = 0
    for obs in observations:
        history.add(obs)
        state = semantic_state(obs, game_map, history, "ENGAGE")
        text = json.dumps(state)
        longest = max(longest, len(text))
        assert len(text) < 2000, f"frame {obs['frame']}: {len(text)} characters"
        assert not list(floats_in(state)), f"frame {obs['frame']}: a float in {state}"
        assert not re.search(r"\d\.\d", text), f"frame {obs['frame']}: a decimal in {text}"

    assert len(observations) > 300
    assert longest > 100  # the states are real content, not empty dicts


def test_the_first_recorded_state_matches_a_hand_calculation():
    # idle_seed7, frame 1: the player is at (26.5, 11.5) facing north (0, -1). The nearest of
    # the three grunts is (25.36, 8.58): 1.14 to the left and 2.92 ahead, so 3.13 away at
    # -21.3 degrees. That is under 22.5, so "ahead" (a hair from "ahead-left"), and "medium".
    rows = [json.loads(line) for line in (FIXTURES / "idle_seed7.jsonl").read_text().splitlines()]

    state = semantic_state(rows[1], rows[0]["map"], HpHistory(), "ENGAGE")

    assert state["threats"]["nearest"] == {
        "direction": "ahead", "distance": "medium", "kind": "grunt", "wounded": False}
    assert state["threats"]["remaining"] == 3
    assert state["progress"] == {"wave": "1 of 3", "boss_present": False}
