"""The harder maps of T8b (tasks.md) must be playable by the agent.

`problems` is the check itself; the tests run it on every file in agent/maps/ and, so that it is known to
be able to fail, on maps that are wrong in one way each.
"""

from collections import deque
from pathlib import Path

import pytest

from kube_agent.config import REPO_ROOT

MAPS = sorted((REPO_ROOT / "agent" / "maps").glob("*.cub"))
CHARSET = set("01NSEW")  # the bonus charset without the door: the bridge has no command to open one
TEXTURE_KEYS = ("NO", "SO", "WE", "EA")
MAX_SIDE = 63  # the game wants fewer than 64 rows and columns (flow-field guard)


def problems(text: str, repo_root: Path = REPO_ROOT) -> list[str]:
    """What is wrong with a map file for this agent, as sentences. An empty list means nothing is."""
    header, _, body = text.partition("\n\n")
    found, grid = [], [row for row in body.splitlines() if row]
    keys = {line.split(" ", 1)[0]: line.split(" ", 1)[1] if " " in line else "" for line in header.splitlines() if line}

    for key in TEXTURE_KEYS:
        path = keys.get(key, "")
        if not path or not (repo_root / path.removeprefix("./")).is_file():
            found.append(f"{key} has no texture file ({path!r})")
    for key in ("F", "C"):
        parts = keys.get(key, "").split(",")
        if len(parts) != 3 or not all(part.strip().isdigit() and int(part) <= 255 for part in parts):
            found.append(f"{key} is not a colour ({keys.get(key)!r})")

    if not grid:
        return found + ["there is no map"]
    if len({len(row) for row in grid}) != 1:
        return found + ["the rows are not all the same length"]
    rows, columns = len(grid), len(grid[0])
    if rows > MAX_SIDE or columns > MAX_SIDE:
        found.append(f"{rows} rows by {columns} columns: the game wants fewer than 64 of each")
    extra = sorted(set("".join(grid)) - CHARSET)
    if extra:
        found.append(f"characters outside 01NSEW: {extra} (a door, for one, cannot be opened by the bridge)")
        return found
    starts = [(x, y) for y, row in enumerate(grid) for x, cell in enumerate(row) if cell in "NSEW"]
    if len(starts) != 1:
        return found + [f"{len(starts)} starting points, there must be one"]
    edge = grid[0] + grid[-1] + "".join(row[0] + row[-1] for row in grid)
    if set(edge) != {"1"}:
        found.append("the border of the map is not all wall")

    floor = {(x, y) for y, row in enumerate(grid) for x, cell in enumerate(row) if cell != "1"}
    reached, queue = {starts[0]}, deque([starts[0]])
    while queue:
        x, y = queue.popleft()
        for step in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            neighbour = (x + step[0], y + step[1])
            if neighbour in floor and neighbour not in reached:
                reached.add(neighbour)
                queue.append(neighbour)
    if reached != floor:
        found.append(f"{len(floor) - len(reached)} floor cells cannot be reached from the start")
    return found


HEADER = "NO ./files/wall_bunker_ns.xpm\nSO ./files/wall_bunker_ns.xpm\nWE ./files/wall_bunker_ew.xpm\nEA ./files/wall_bunker_ew.xpm\nF 120,120,115\nC 40,40,45\n\n"
GOOD = ["1111111", "1000001", "10N0001", "1000001", "1111111"]


def with_grid(rows: list[str], header: str = HEADER) -> str:
    return header + "\n".join(rows) + "\n"


# --- the maps that are in the repository ---------------------------------------------------------


def test_the_repository_has_at_least_one_harder_map():
    assert MAPS, "agent/maps/ holds no .cub file"


@pytest.mark.parametrize("path", MAPS, ids=[path.name for path in MAPS])
def test_every_harder_map_passes_the_checks(path):
    assert problems(path.read_text()) == []


# --- the check can fail: one wrong thing at a time ----------------------------------------------


def test_a_good_map_has_no_problems():
    assert problems(with_grid(GOOD)) == []


def test_a_door_is_refused():
    assert any("D" in p for p in problems(with_grid(["1111111", "1000001", "10N0D01", "1000001", "1111111"])))


def test_no_starting_point_is_refused():
    assert problems(with_grid(["1111111", "1000001", "1000001", "1000001", "1111111"])) == ["0 starting points, there must be one"]


def test_two_starting_points_are_refused():
    assert problems(with_grid(["1111111", "1S00001", "10N0001", "1000001", "1111111"])) == ["2 starting points, there must be one"]


def test_floor_the_player_cannot_reach_is_refused():
    walled_off = ["1111111", "1001001", "10N1001", "1001001", "1111111"]  # a wall splits the room in two

    assert problems(with_grid(walled_off)) == ["6 floor cells cannot be reached from the start"]


def test_floor_that_touches_the_start_only_at_a_corner_is_refused():
    # The agent walks the map with 4 neighbours, so a room joined to the start only diagonally is out of reach.
    diagonal = ["1111111", "1001111", "10N1111", "1110011", "1110011", "1111111", "1111111"]

    assert problems(with_grid(diagonal)) == ["4 floor cells cannot be reached from the start"]


def test_a_border_that_is_not_all_wall_is_refused():
    assert problems(with_grid(["1111111", "1000001", "00N0001", "1000001", "1111111"])) == ["the border of the map is not all wall"]


def test_rows_of_different_length_are_refused():
    assert problems(with_grid(["1111111", "100001", "10N0001", "1000001", "1111111"])) == ["the rows are not all the same length"]


@pytest.mark.parametrize("rows, columns", [(64, 10), (10, 64)])
def test_a_map_of_64_rows_or_columns_is_refused(rows, columns):
    grid = ["1" * columns] + ["1" + "0" * (columns - 2) + "1" for _ in range(rows - 2)] + ["1" * columns]
    grid[1] = "1N" + "0" * (columns - 3) + "1"

    assert any("fewer than 64" in p for p in problems(with_grid(grid)))


def test_a_map_of_63_by_63_is_allowed():
    grid = ["1" * 63] + ["1" + "0" * 61 + "1" for _ in range(61)] + ["1" * 63]
    grid[1] = "1N" + "0" * 60 + "1"

    assert problems(with_grid(grid)) == []


def test_a_texture_that_does_not_exist_is_refused():
    header = HEADER.replace("wall_bunker_ew.xpm", "no_such_wall.xpm")

    assert len(problems(with_grid(GOOD, header))) == 2  # the WE and the EA lines


def test_a_missing_colour_is_refused():
    header = HEADER.replace("F 120,120,115\n", "")

    assert problems(with_grid(GOOD, header)) == ["F is not a colour (None)"]


@pytest.mark.parametrize("colour", ["120,120", "1,2,3,4"])
def test_a_colour_with_the_wrong_number_of_parts_is_refused(colour):
    header = HEADER.replace("F 120,120,115", f"F {colour}")

    assert problems(with_grid(GOOD, header)) == [f"F is not a colour ('{colour}')"]


def test_a_colour_out_of_range_is_refused():
    header = HEADER.replace("C 40,40,45", "C 40,40,300")

    assert problems(with_grid(GOOD, header)) == ["C is not a colour ('40,40,300')"]


def test_a_file_with_no_map_is_refused():
    assert problems(HEADER) == ["there is no map"]
