import math

import pytest
from helpers import ROOM, enemy, enemy_ahead, make_obs, player

from kube_agent.controller import (
    Controller,
    movement_flags,
    pick_target,
    reachable,
    should_fire,
    turn_toward,
)

KEYS = ["forward", "back", "strafe_left", "strafe_right", "turn_left", "turn_right", "fire"]

# Hand-made maps. Floor is 0, walls 1; (column, row) counts from the top left.
CORRIDOR = ["1111111", "1000001", "1111111"]  # floor: row 1, columns 1 to 5
BOX = ["1111111", "1000001", "1000001", "1000001", "1111111"]  # floor: rows 1-3, columns 1-5
RING = ["1111111", "1000001", "1011101", "1000001", "1111111"]  # a ring round a block
HOOK = ["1111111", "1000001", "1011101", "1111111"]  # columns 1 and 5 of row 2 joined only by row 1
TWO_ROOMS = ["111111111", "100010001", "100010001", "111111111"]  # no way from one room to the other


def flags(line):
    parts = line.split()
    assert parts[0] == "C" and len(parts) == 8, line
    return {key: int(value) for key, value in zip(KEYS, parts[1:])}


def decide(enemies, tactic="ENGAGE", game_map=ROOM, **fields):
    """The line a fresh controller wants for one observation (the default player faces east)."""
    return Controller(game_map).decide(make_obs(enemies, **fields), tactic)


# --- turning ------------------------------------------------------------------------------------


@pytest.mark.parametrize("ahead, right, expected", [
    (5.0, 1.0, (False, True)),  # on the right: turn right
    (5.0, -1.0, (True, False)),
    (-3.0, 0.0, (False, True)),  # straight behind: on a tie, right
    (-3.0, -0.5, (True, False)),
    (-3.0, 0.5, (False, True)),
    (0.0, 2.0, (False, True)),  # exactly abreast counts as behind
    (0.0, 0.1, (False, True)),  # even a hair off the line: abreast is not "ahead", so it turns
    (5.0, 0.0, (False, False)),
    (5.0, 0.24, (False, False)),  # inside the dead zone of 0.25 cells: no turn
    (5.0, -0.24, (False, False)),
    (5.0, 0.25, (False, True)),  # the edge of the zone turns
    (5.0, -0.25, (True, False)),
])
def test_turn_toward_the_side_of_the_target_outside_the_dead_zone(ahead, right, expected):
    assert turn_toward(player(), enemy_ahead(ahead, right)) == expected


def test_a_far_target_a_hair_off_the_line_is_turned_toward_and_not_ignored():
    # 9.5 cells ahead and 0.049 rad off the aim line: 0.47 cells off, outside the 0.45 fire
    # margin. An angular dead zone of 0.05 rad would neither turn nor fire, and the player
    # would stand there for ever.
    right = 9.5 * math.tan(0.049)
    assert math.atan2(right, 9.5) < 0.05 and right > 0.45  # the premise of the test

    keys = flags(decide([enemy_ahead(9.5, right)]))

    assert keys["turn_right"] == 1
    assert keys["fire"] == 0


def test_it_fires_while_still_settling_the_aim():
    keys = flags(decide([enemy_ahead(9.5, 0.3)]))  # 0.3 is outside the 0.25 zone, inside the 0.45 margin

    assert keys["turn_right"] == 1
    assert keys["fire"] == 1


# --- firing -------------------------------------------------------------------------------------


def fire_decision(ahead=5.0, right=0.1, weapon_ready=1, los=1):
    return should_fire(player(), enemy_ahead(ahead, right, los=los), weapon_ready)


def test_it_fires_when_every_condition_holds():
    assert fire_decision() is True


@pytest.mark.parametrize("change", [
    {"los": 0}, {"ahead": 0.0}, {"ahead": -2.0}, {"ahead": 10.0},
    {"right": 0.46}, {"right": -0.46}, {"weapon_ready": 0},
])
def test_it_does_not_fire_when_any_single_condition_fails(change):
    assert fire_decision(**change) is False


@pytest.mark.parametrize("change", [{"ahead": 9.99}, {"ahead": 0.01}, {"right": 0.44}, {"right": -0.44}])
def test_it_fires_just_inside_each_limit(change):
    assert fire_decision(**change) is True


def test_it_does_not_fire_with_no_target():
    assert should_fire(player(), None, 1) is False


# --- the target ---------------------------------------------------------------------------------


def test_the_target_is_the_nearest_enemy_with_line_of_sight():
    hidden_near = enemy_ahead(2.0, 0.0, los=0)
    seen = enemy_ahead(6.0, 1.0, los=1)
    seen_farther = enemy_ahead(8.0, 0.0, los=1)

    assert pick_target(player(), [hidden_near, seen_farther, seen]) is seen


def test_with_no_line_of_sight_the_target_is_the_nearest_enemy():
    near = enemy_ahead(2.0, 0.0, los=0)
    far = enemy_ahead(6.0, 0.0, los=0)

    assert pick_target(player(), [far, near]) is near


def test_no_enemies_no_target():
    assert pick_target(player(), []) is None


# --- movement flags -----------------------------------------------------------------------------


@pytest.mark.parametrize("w, expected", [
    ((1.0, 0.0), (1, 0, 0, 0)),  # east, facing east: forward
    ((-1.0, 0.0), (0, 1, 0, 0)),
    ((0.0, 1.0), (0, 0, 0, 1)),  # south is on the right of an east-facing player
    ((0.0, -1.0), (0, 0, 1, 0)),
    ((1.0, 1.0), (1, 0, 0, 1)),  # a diagonal presses two keys
    ((-1.0, -1.0), (0, 1, 1, 0)),
    ((0.0, 0.0), (0, 0, 0, 0)),
])
def test_movement_flags_facing_east(w, expected):
    assert tuple(map(int, movement_flags(player(), w))) == expected


@pytest.mark.parametrize("dx, dy, w, expected", [
    (0.0, -1.0, (1.0, 0.0), (0, 0, 0, 1)),  # facing north, east is on the right
    (0.0, -1.0, (0.0, -1.0), (1, 0, 0, 0)),
    (0.0, 1.0, (-1.0, 0.0), (0, 0, 0, 1)),  # facing south, west is on the right
    (-1.0, 0.0, (0.0, -1.0), (0, 0, 0, 1)),  # facing west, north is on the right
])
def test_movement_flags_follow_the_heading(dx, dy, w, expected):
    assert tuple(map(int, movement_flags(player(dx=dx, dy=dy), w))) == expected


def test_the_vector_is_normalised_before_the_threshold():
    # 0.2 is under the 0.3 threshold, but as a direction it is straight ahead.
    assert movement_flags(player(), (0.2, 0.0)) == (True, False, False, False)
    assert movement_flags(player(), (20.0, 0.0)) == (True, False, False, False)


@pytest.mark.parametrize("side, strafes", [(0.29, False), (0.31, True)])
def test_the_threshold_of_0_3_is_on_the_unit_vector(side, strafes):
    w = (math.sqrt(1 - side * side), side)

    assert movement_flags(player(), w)[3] is strafes  # index 3 is strafe right


# --- the tactics, through decide() --------------------------------------------------------------


def test_engage_holds_still_and_fires():
    assert decide([enemy_ahead(5.0, 0.0)], "ENGAGE") == "C 0 0 0 0 0 0 1"


def test_engage_only_turns_when_the_target_is_off_to_the_side():
    assert decide([enemy_ahead(4.0, 3.0)], "ENGAGE") == "C 0 0 0 0 0 1 0"


def test_with_no_enemies_every_tactic_holds_still():
    for tactic in ("ENGAGE", "KITE", "RETREAT", "SEARCH"):
        assert decide([], tactic) == "C 0 0 0 0 0 0 0"


def test_kite_backs_away_from_the_target():
    assert decide([enemy_ahead(3.0, 0.0)], "KITE") == "C 0 1 0 0 0 0 1"


def test_kite_backs_and_strafes_away_from_a_diagonal_target():
    # The target is south-east, so away is north-west: back, and left (north, facing east).
    assert decide([enemy_ahead(3.0, 3.0)], "KITE") == "C 0 1 1 0 0 1 0"


def test_kite_with_a_wall_behind_falls_back_to_the_retreat_vector():
    target = enemy(4.5, 3.5)  # from (1.5, 2.5) facing east: 3 ahead, 1 to the right
    in_the_box = flags(Controller(BOX).decide(make_obs([target], x=1.5, y=2.5), "KITE"))
    in_the_open = flags(decide([enemy_ahead(3.0, 1.0)], "KITE"))

    # Backwards is a wall: the retreat goes round it (north, i.e. strafe left).
    assert (in_the_box["back"], in_the_box["strafe_left"]) == (0, 1)
    assert (in_the_open["back"], in_the_open["strafe_left"]) == (1, 1)  # in the open it backs away


def test_retreat_runs_away_along_a_corridor_and_turns_to_face_the_threat():
    behind = enemy(1.5, 1.5)
    ahead = enemy(5.5, 1.5)

    assert Controller(CORRIDOR).decide(make_obs([behind], x=3.5, y=1.5), "RETREAT") == "C 1 0 0 0 0 1 0"
    assert Controller(CORRIDOR).decide(make_obs([ahead], x=3.5, y=1.5), "RETREAT") == "C 0 1 0 0 0 0 1"


def test_retreat_stays_when_its_own_cell_is_the_farthest():
    # At the dead end the farthest cell from the threat is the player's own.
    line = Controller(CORRIDOR).decide(make_obs([enemy(1.5, 1.5)], x=5.5, y=1.5), "RETREAT")

    assert line == "C 0 0 0 0 0 1 0"  # no movement, only the turn to face it


def test_retreat_prefers_the_nearer_cell_when_two_are_equally_far():
    # From (2.5, 1.5) with the threat at (3.5, 1.5), both ends of the corridor are 2.0 away:
    # column 1 is one step off and column 5 three, so it goes west, not through the threat.
    line = Controller(CORRIDOR).decide(make_obs([enemy(3.5, 1.5)], x=2.5, y=1.5), "RETREAT")

    assert line == "C 0 1 0 0 0 0 1"


def test_retreat_goes_round_an_obstacle_to_the_farthest_cell():
    # Threat at (3.5, 1.5) on the top of the ring: the farthest corners are on the bottom row,
    # and the first step from (1.5, 2.5) is south, which is the right of an east-facing player.
    line = Controller(RING).decide(make_obs([enemy(3.5, 1.5)], x=1.5, y=2.5), "RETREAT")

    assert line == "C 0 0 0 1 1 0 0"


def test_retreat_only_looks_eight_steps_ahead():
    # A corridor of 21 cells. The player is at column 8 with the threat 2 cells east. Within 8
    # steps the farthest cell is column 1 (9.0 from the threat) to the west; without the limit it
    # would be column 21 (11.0), through the threat.
    corridor = ["1" * 23, "1" + "0" * 21 + "1", "1" * 23]

    line = Controller(corridor).decide(make_obs([enemy(10.5, 1.5)], x=8.5, y=1.5), "RETREAT")

    assert line == "C 0 1 0 0 0 0 1"


def test_search_walks_along_a_corridor_toward_the_enemy():
    line = Controller(CORRIDOR).decide(make_obs([enemy(5.5, 1.5, los=0)], x=1.5, y=1.5), "SEARCH")

    assert line == "C 1 0 0 0 0 0 0"


def test_search_aims_at_the_next_cell_of_the_path_and_not_at_the_enemy():
    # The enemy is dead ahead through a wall, but the only way there starts to the north.
    line = Controller(HOOK).decide(make_obs([enemy(5.5, 2.5, los=0)], x=1.5, y=2.5), "SEARCH")

    assert line == "C 0 0 1 0 1 0 0"  # strafe left and turn left; aiming at the enemy would not turn


def test_search_does_not_move_when_the_enemy_is_in_the_players_cell():
    line = flags(decide([enemy(5.9, 5.8, los=0)], "SEARCH"))

    assert (line["forward"], line["back"], line["strafe_left"], line["strafe_right"]) == (0, 0, 0, 0)
    assert line["turn_right"] == 1  # it still aims at the enemy


def test_search_does_not_move_when_there_is_no_path():
    line = Controller(TWO_ROOMS).decide(make_obs([enemy(6.5, 1.5, los=0)], x=1.5, y=1.5), "SEARCH")

    assert line == "C 0 0 0 0 0 0 0"


def test_search_heads_for_the_nearest_enemy_even_if_a_farther_one_is_in_view():
    near_hidden = enemy(3.5, 5.5, los=0)  # 2 cells west
    far_seen = enemy(10.5, 5.5, los=1)  # 5 cells east

    keys = flags(decide([near_hidden, far_seen], "SEARCH"))

    assert (keys["forward"], keys["back"]) == (0, 1)


def test_an_unknown_tactic_is_an_error_that_names_it():
    with pytest.raises(ValueError, match="tactic 'FLEE'"):
        decide([], "FLEE")


# --- the breadth-first search -------------------------------------------------------------------


def test_reachable_counts_the_steps_and_remembers_the_first_one():
    found = reachable(CORRIDOR, (1, 1))

    assert found[(1, 1)] == (0, None)
    assert found[(4, 1)] == (3, (2, 1))
    assert len(found) == 5


def test_reachable_stops_at_the_depth_limit():
    long_corridor = ["1" * 22, "1" + "0" * 20 + "1", "1" * 22]

    found = reachable(long_corridor, (1, 1), max_depth=8)

    assert max(steps for steps, _ in found.values()) == 8
    assert len(found) == 9


def test_reachable_does_not_cross_walls_or_closed_doors():
    assert set(reachable(["11111", "10D01", "11111"], (1, 1))) == {(1, 1)}
    assert set(reachable(["11111", "10O01", "11111"], (1, 1))) == {(1, 1), (2, 1), (3, 1)}


# --- stuck detection ----------------------------------------------------------------------------

STILL = [(index / 10, 5.5, 5.5) for index in range(10)]  # 0.9 s without moving


def lines_for(path, game_map=ROOM, tactic="SEARCH"):
    controller = Controller(game_map)
    hidden = enemy(10.5, 5.5, los=0)  # SEARCH walks east along row 5
    return [flags(controller.decide(make_obs([hidden], t=t, x=x, y=y), tactic)) for t, x, y in path]


def test_a_player_that_does_not_move_for_half_a_second_gets_a_strafe_toward_an_open_side():
    lines = lines_for(STILL)

    assert [line["forward"] for line in lines] == [1] * 10
    # It cannot know before it has 0.5 s of history; from t=0.5 on it strafes (right is preferred).
    assert [line["strafe_right"] for line in lines] == [0] * 5 + [1] * 5
    assert not any(line["strafe_left"] for line in lines)


def test_the_unsticking_strafe_replaces_the_one_the_path_asked_for():
    # The enemy is due north, so the path says strafe left; both sides are open, and the
    # unsticking strafe goes right. Pressing both keys would cancel out.
    controller = Controller(ROOM)
    north = enemy(5.5, 2.5, los=0)
    lines = [flags(controller.decide(make_obs([north], t=t, x=x, y=y), "SEARCH")) for t, x, y in STILL]

    assert [(line["strafe_left"], line["strafe_right"]) for line in lines] == [(1, 0)] * 5 + [(0, 1)] * 5


def test_a_player_that_is_moving_is_not_stuck():
    moving = [(index / 10, 5.5 + 0.12 * index, 5.5) for index in range(10)]

    assert not any(line["strafe_right"] or line["strafe_left"] for line in lines_for(moving))


def test_the_strafe_lasts_half_a_second():
    # Still until t=0.5 (stuck is seen), then it moves south by 0.1 a step.
    path = STILL[:6] + [(0.6 + step / 10, 5.5, 5.5 + 0.1 * (step + 1)) for step in range(6)]

    lines = lines_for(path)

    assert [line["strafe_right"] for line in lines] == [0] * 5 + [1] * 5 + [0] * 2  # t=1.0 and 1.1: moved


def test_it_strafes_to_the_left_when_only_the_left_is_open():
    rows = list(ROOM)
    rows[6] = "100001000000"  # a wall south of the player, which is the right of an east-facing one

    lines = lines_for(STILL, rows)

    assert [line["strafe_left"] for line in lines] == [0] * 5 + [1] * 5
    assert not any(line["strafe_right"] for line in lines)


def test_it_adds_nothing_when_neither_side_is_open():
    rows = list(ROOM)
    rows[6] = "100001000000"
    rows[4] = "100001000000"

    assert not any(line["strafe_right"] or line["strafe_left"] for line in lines_for(STILL, rows))


def test_a_player_that_wants_to_stand_still_is_never_stuck():
    lines = []
    controller = Controller(ROOM)
    for t, x, y in STILL:
        lines.append(flags(controller.decide(make_obs([enemy(10.5, 5.5)], t=t, x=x, y=y), "ENGAGE")))

    assert not any(line["strafe_right"] or line["strafe_left"] for line in lines)


# --- no repeated lines --------------------------------------------------------------------------


def test_command_sends_a_line_only_when_it_changes():
    controller = Controller(ROOM)
    ready = make_obs([enemy_ahead(5.0, 0.0)])
    reloading = make_obs([enemy_ahead(5.0, 0.0)], weapon_ready=0)

    assert controller.command(ready, "ENGAGE") == "C 0 0 0 0 0 0 1"
    assert controller.command(ready, "ENGAGE") is None
    assert controller.command(reloading, "ENGAGE") == "C 0 0 0 0 0 0 0"
    assert controller.command(reloading, "ENGAGE") is None
    assert controller.command(ready, "ENGAGE") == "C 0 0 0 0 0 0 1"  # an earlier line again is a change


def test_the_game_starts_with_no_key_held_so_a_first_all_zero_line_is_not_sent():
    assert Controller(ROOM).command(make_obs([]), "ENGAGE") is None
