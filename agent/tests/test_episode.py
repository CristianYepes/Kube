import asyncio
import hashlib
import io
import json
import platform
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import pytest
from helpers import make_obs

from kube_agent import config, episode
from kube_agent.bridge import BridgeError, GameBridge
from kube_agent.config import DEFAULT_MAP, REPO_ROOT
from kube_agent.controller import Controller
from kube_agent.episode import STALL_SECONDS, StallCounter, Tally, play, run_episode
from kube_agent.policies import make_policy

TESTS = Path(__file__).resolve().parent
FIXTURE = TESTS / "fixtures" / "idle_seed7.jsonl"
FAKE_GAME = TESTS / "fake_game.py"
OBSERVATIONS = [json.loads(line) for line in FIXTURE.read_text().splitlines()][1:]
GUARD_SECONDS = 30  # a loop that hangs must fail the test, not freeze pytest
RESULT_FIELDS = {
    "run_id", "policy", "seed", "map", "map_sha256", "machine", "runner", "config_sha256",
    "max_seconds", "outcome", "survival_seconds", "wave_reached", "kills", "damage_taken",
    "drops", "stalls", "tactic_seconds", "switches", "decisions", "decisions_applied", "spend_usd",
}


def run(coroutine):
    return asyncio.run(asyncio.wait_for(coroutine, GUARD_SECONDS))


def fake_command(folder, fixture=FIXTURE, mode="normal"):
    folder.mkdir(parents=True, exist_ok=True)
    return [sys.executable, str(FAKE_GAME), str(fixture), str(folder / "stdin_seen.txt"), mode]


def stdin_seen(folder):
    return (folder / "stdin_seen.txt").read_text().splitlines()


async def play_fixture(folder, policy_name, max_seconds, fixture=FIXTURE, wrap=lambda controller: controller):
    async with GameBridge(fake_command(folder, fixture)) as game:
        game_map = game.init["map"]
        policy = make_policy(policy_name, game_map)
        controller = wrap(Controller(game_map))
        episode_file, decisions_file = io.StringIO(), io.StringIO()
        result = await play(game, policy, controller, episode_file, decisions_file, max_seconds)
    return result, episode_file.getvalue(), decisions_file.getvalue()


def jsonl(text):
    return [json.loads(line) for line in text.splitlines()]


# --- stalls (AC8) -------------------------------------------------------------------------------


class FakeClock:
    def __init__(self, times):
        self._times = iter(times)

    def __call__(self):
        return next(self._times)


def test_a_gap_above_a_tenth_of_a_second_between_observations_is_a_stall():
    counter = StallCounter(FakeClock([0.0, 0.0625, 0.125, 0.25, 0.3125, 0.5]))

    for _ in range(6):
        counter.tick()

    assert counter.count == 2  # the gaps 0.125 and 0.1875; the others are 0.0625


def test_the_first_observation_is_not_a_stall():
    counter = StallCounter(FakeClock([1000.0]))
    counter.tick()

    assert counter.count == 0


def test_a_gap_of_exactly_the_limit_is_not_a_stall_and_a_hair_more_is():
    # The clock starts at 0.0 because (1000.0 + 0.1) - 1000.0 is not exactly 0.1 in floating point.
    at_the_limit = StallCounter(FakeClock([0.0, STALL_SECONDS]))
    over_it = StallCounter(FakeClock([0.0, STALL_SECONDS * 1.01]))
    for counter in (at_the_limit, over_it):
        counter.tick()
        counter.tick()

    assert (at_the_limit.count, over_it.count) == (0, 1)


def test_a_loop_that_blocks_for_a_moment_between_observations_is_counted():
    counter = StallCounter()
    for _ in range(3):
        for _ in range(10):
            counter.tick()
            time.sleep(0.005)
        counter.tick()
        time.sleep(0.15)  # the block
    counter.tick()

    assert counter.count >= 3  # a loaded machine can only add stalls, never remove them


# --- the tally ----------------------------------------------------------------------------------


def obs_with(enemies=0, hp=100, wave=1, t=0.0, dt=0.01, drops=0):
    obs = make_obs([{"x": 1.0, "y": 1.0, "type": 0, "hp": 2, "ai": 1, "los": 1}] * enemies, hp=hp, wave=wave, t=t)
    obs["dt"], obs["drops"] = dt, drops
    return obs


def test_damage_cannot_exceed_the_hp_the_player_had():
    # The game lets hp fall below zero (a recorded idle player ends at -10).
    tally = Tally()
    for hp in (100, 10, -10):
        tally.observe(obs_with(hp=hp), None)

    assert tally.damage == 100


def test_damage_is_the_hp_lost_and_a_rise_is_not_negative_damage():
    tally = Tally()
    for hp in (100, 90, 90, 95, 70):
        tally.observe(obs_with(hp=hp), None)

    assert tally.damage == 10 + 25


def test_a_whole_game_is_eight_kills():
    # 3 grunts, 4 runners and the boss. The game starts the next wave only when none is left, and
    # on the same frame, so the last enemy of a wave dies as the count jumps up with the new wave.
    tally = Tally()
    for wave, enemies in [(1, 3), (1, 2), (1, 2), (1, 1), (2, 4), (2, 3), (2, 2), (2, 1), (3, 1), (3, 0)]:
        tally.observe(obs_with(enemies=enemies, wave=wave), None)

    assert tally.kills == 8


def test_an_enemy_count_that_rises_within_a_wave_is_not_a_kill():
    tally = Tally()
    for enemies in (3, 5, 4):
        tally.observe(obs_with(enemies=enemies, wave=1), None)

    assert tally.kills == 1  # only the 5 -> 4


def test_the_tally_keeps_the_last_time_the_highest_wave_and_the_drops():
    tally = Tally()
    tally.observe(obs_with(t=1.0, wave=1, drops=0), None)
    tally.observe(obs_with(t=2.5, wave=3, drops=2, enemies=2), None)
    tally.observe(obs_with(t=3.0, wave=2, drops=7), None)  # cannot happen in the game; the max is kept

    assert (tally.survival, tally.wave, tally.drops) == (3.0, 3, 7)
    assert tally.kills == 0  # a wave number going backwards invents no kills


def test_time_is_counted_per_tactic_and_none_counts_nowhere():
    tally = Tally()
    for tactic, dt in [("ENGAGE", 0.25), ("ENGAGE", 0.25), ("KITE", 0.5), (None, 1.0)]:
        tally.observe(obs_with(dt=dt), tactic)

    assert tally.tactic_seconds == {"ENGAGE": 0.5, "KITE": 0.5}


def decision_row(before, after, applied=True, **extra):
    return {"t": 0.0, "state": {"current_tactic": before}, "tactic": after, "applied": applied, **extra}


def test_decisions_are_counted_and_a_switch_is_an_applied_change_of_tactic():
    tally = Tally()
    tally.decision(decision_row("ENGAGE", "ENGAGE"))  # a decision that keeps the tactic
    tally.decision(decision_row("ENGAGE", "KITE"))  # a switch
    tally.decision(decision_row("KITE", "RETREAT", applied=False))  # asked for, not applied: no switch
    tally.decision(decision_row("KITE", "SEARCH", cost=0.002))

    assert (tally.decisions, tally.applied, tally.switches) == (4, 3, 2)
    assert tally.spend == pytest.approx(0.002)


# --- play(): one episode over a recorded game ---------------------------------------------------


def test_the_episode_ends_at_the_time_limit(tmp_path):
    result, _, _ = run(play_fixture(tmp_path, "idle", 2.0))

    assert result["outcome"] == "timeout"
    assert 2.0 <= result["survival_seconds"] < 2.1


@pytest.mark.parametrize("state, outcome", [(1, "lose"), (2, "win")])
def test_the_episode_ends_when_the_game_does(tmp_path, state, outcome):
    lines = FIXTURE.read_text().splitlines()
    changed = [lines[0]]
    for line in lines[1:]:
        obs = json.loads(line)
        obs["state"] = state if obs["frame"] >= 150 else 0
        changed.append(json.dumps(obs))
    fixture = tmp_path / "ends.jsonl"
    fixture.write_text("\n".join(changed) + "\n")

    result, _, _ = run(play_fixture(tmp_path, "idle", 4.5, fixture=fixture))

    assert result["outcome"] == outcome
    assert result["survival_seconds"] == round(OBSERVATIONS[149]["t"], 2)  # frame 150, not later


def test_idle_sends_the_game_nothing_but_the_quit_line(tmp_path):
    run(play_fixture(tmp_path, "idle", 2.0))

    assert stdin_seen(tmp_path) == ["Q"]


def test_scripted_sends_valid_command_lines_and_never_the_same_twice_in_a_row(tmp_path):
    run(play_fixture(tmp_path, "scripted", 2.0))

    lines = stdin_seen(tmp_path)
    commands = lines[:-1]
    assert lines[-1] == "Q"
    assert commands  # it did act
    assert all(re.fullmatch(r"C [01]( [01]){6}", line) for line in commands)
    assert all(a != b for a, b in zip(commands, commands[1:]))
    assert commands[0] != "C 0 0 0 0 0 0 0"  # the game starts with no key held, so that is never sent


def test_the_episode_log_has_a_row_about_every_half_second(tmp_path):
    result, episode_text, _ = run(play_fixture(tmp_path, "scripted", 2.0))

    rows = jsonl(episode_text)
    assert all(set(row) == {"t", "x", "y", "hp", "wave", "enemies", "tactic"} for row in rows)
    assert rows[0]["t"] == 0.0
    assert rows[-1]["t"] == result["survival_seconds"]  # the last row is where the episode ended
    times = [row["t"] for row in rows]
    assert all(b - a >= 0.49 for a, b in zip(times, times[1:-1]))  # the final row may come sooner
    assert 4 <= len(rows) <= 6
    assert all(row["x"] == round(row["x"], 2) and row["y"] == round(row["y"], 2) for row in rows)
    assert all(row["enemies"] == 3 and row["wave"] == 1 for row in rows)
    assert {row["tactic"] for row in rows} <= {"ENGAGE", "KITE", "RETREAT", "SEARCH"}


def test_idle_rows_have_no_tactic_and_its_decision_log_is_empty(tmp_path):
    _, episode_text, decisions_text = run(play_fixture(tmp_path, "idle", 2.0))

    assert {row["tactic"] for row in jsonl(episode_text)} == {None}
    assert decisions_text == ""


def test_the_decision_log_of_scripted_has_the_documented_rows(tmp_path):
    result, _, decisions_text = run(play_fixture(tmp_path, "scripted", 2.0))

    decisions = jsonl(decisions_text)
    assert all(set(row) == {"t", "state", "tactic", "applied"} for row in decisions)
    assert len(decisions) == result["decisions"] == result["decisions_applied"]
    assert len(decisions) >= 4  # at 0.0, 0.5, 1.0 and 1.5 s
    assert result["spend_usd"] == 0.0


def test_the_result_is_what_the_recording_says(tmp_path):
    # An oracle: the same numbers computed straight from the recorded observations.
    seen = []
    for obs in OBSERVATIONS:
        seen.append(obs)
        if obs["t"] >= 4.5:
            break
    damage = sum(max(0, a["hp"] - b["hp"]) for a, b in zip(seen, seen[1:]))
    assert damage > 0  # the recorded player does lose hp, so this checks something

    result, _, _ = run(play_fixture(tmp_path, "idle", 4.5))

    assert result["damage_taken"] == damage
    assert (result["kills"], result["wave_reached"], result["drops"]) == (0, 1, 0)
    assert (result["decisions"], result["switches"], result["tactic_seconds"]) == (0, 0, {})
    assert result["survival_seconds"] == round(seen[-1]["t"], 2)


def test_scripted_spends_its_time_in_tactics_that_add_up_to_the_episode(tmp_path):
    result, _, _ = run(play_fixture(tmp_path, "scripted", 2.0))

    assert set(result["tactic_seconds"]) <= {"ENGAGE", "KITE", "RETREAT", "SEARCH"}
    assert sum(result["tactic_seconds"].values()) == pytest.approx(result["survival_seconds"], abs=0.05)


class SlowController:
    """Blocks the loop for a moment every `every` calls, as a slow agent would."""

    def __init__(self, inner, every, block):
        self._inner, self._every, self._block, self._calls = inner, every, block, 0

    def command(self, obs, tactic):
        self._calls += 1
        if self._calls % self._every == 0:
            time.sleep(self._block)
        return self._inner.command(obs, tactic)


def test_a_slow_controller_shows_up_in_the_stalls_of_the_result(tmp_path):
    normal, _, _ = run(play_fixture(tmp_path / "normal", "scripted", 2.0))
    slow, _, _ = run(play_fixture(tmp_path / "slow", "scripted", 2.0,
                                  wrap=lambda controller: SlowController(controller, every=40, block=0.15)))

    assert slow["stalls"] >= normal["stalls"] + 4  # about 190 observations, one block per 40


def test_a_game_whose_output_ends_before_the_episode_is_an_error_of_play_itself(tmp_path):
    # The stand-in exits with code 0, so close() has nothing to complain about: the only error
    # that can come out is the one play() raises when the observations stop.
    async def scenario():
        async with GameBridge(fake_command(tmp_path, mode="ends-early")) as game:
            policy = make_policy("idle", game.init["map"])
            await play(game, policy, Controller(game.init["map"]), io.StringIO(), io.StringIO(), 5.0)

    with pytest.raises(BridgeError, match=r"output ended at t=0\.\d+, before the episode did"):
        run(scenario())


def test_positions_in_the_episode_log_have_two_decimals(tmp_path):
    lines = FIXTURE.read_text().splitlines()
    moved = [lines[0]]
    for line in lines[1:]:
        obs = json.loads(line)
        obs["player"]["x"], obs["player"]["y"] = 26.4567, 11.5432
        moved.append(json.dumps(obs))
    fixture = tmp_path / "moved.jsonl"
    fixture.write_text("\n".join(moved) + "\n")

    _, episode_text, _ = run(play_fixture(tmp_path, "idle", 1.0, fixture=fixture))

    assert {(row["x"], row["y"]) for row in jsonl(episode_text)} == {(26.46, 11.54)}


# --- run_episode(): folders, files and failures -------------------------------------------------

FIXED = datetime(2026, 10, 6, 9, 30, 0, tzinfo=timezone.utc)
MACHINE = platform.system().lower()


def run_fake(folder, policy="scripted", seed=7, mode="normal", max_seconds=2.0, utc_now=lambda: FIXED, map_path=DEFAULT_MAP):
    return run(run_episode(
        policy, seed, map_path, "local", max_seconds, runs_dir=folder / "runs", utc_now=utc_now,
        command=fake_command(folder, mode=mode)))


def test_an_episode_writes_its_folder_with_the_three_files_and_the_documented_result(tmp_path):
    result = run_fake(tmp_path)

    run_dir = tmp_path / "runs" / f"20261006T093000Z-scripted-s7-{MACHINE}"
    assert result["run_id"] == run_dir.name
    assert {path.name for path in run_dir.iterdir()} == {"result.json", "episode.jsonl", "decisions.jsonl"}
    assert set(result) == RESULT_FIELDS
    assert json.loads((run_dir / "result.json").read_text()) == result
    assert result["map_sha256"] == hashlib.sha256((REPO_ROOT / DEFAULT_MAP).read_bytes()).hexdigest()
    assert result["config_sha256"] == config.config_sha256()
    assert (result["policy"], result["seed"], result["map"], result["machine"]) == (
        "scripted", 7, DEFAULT_MAP, MACHINE)
    assert len(jsonl((run_dir / "episode.jsonl").read_text())) >= 4
    assert len(jsonl((run_dir / "decisions.jsonl").read_text())) == result["decisions"]


def test_a_run_is_never_overwritten(tmp_path):
    run_fake(tmp_path)
    result_file = tmp_path / "runs" / f"20261006T093000Z-scripted-s7-{MACHINE}" / "result.json"
    before = result_file.read_text()

    with pytest.raises(FileExistsError):
        run_fake(tmp_path)  # the same second, policy, seed and machine

    assert result_file.read_text() == before


def test_a_map_that_does_not_exist_creates_no_folder(tmp_path):
    with pytest.raises(FileNotFoundError):
        run_fake(tmp_path, map_path="maps/does_not_exist.cub")

    assert not (tmp_path / "runs").exists()


def test_an_unknown_policy_creates_no_folder(tmp_path):
    with pytest.raises(ValueError, match="policy 'jev'"):
        run_fake(tmp_path, policy="jev")

    assert not (tmp_path / "runs").exists()


def test_a_game_that_crashes_still_leaves_a_result_that_says_so(tmp_path):
    with pytest.raises(BridgeError):
        run_fake(tmp_path, mode="dies-after-init")

    run_dir = tmp_path / "runs" / f"20261006T093000Z-scripted-s7-{MACHINE}"
    result = json.loads((run_dir / "result.json").read_text())
    assert result["outcome"] == "error"
    assert "exited with code 3" in result["error"]
    assert (run_dir / "episode.jsonl").is_file() and (run_dir / "decisions.jsonl").is_file()


def test_a_game_that_stops_answering_hits_the_wall_clock_limit(tmp_path, monkeypatch):
    # The recording ends at 4.9 s of game time, so asking for 20 s leaves the loop waiting.
    monkeypatch.setattr(episode, "GUARD_FACTOR", 0.0)
    monkeypatch.setattr(episode, "GUARD_SLACK", 1.0)

    with pytest.raises(BridgeError, match="wall-clock"):
        run_fake(tmp_path, max_seconds=20.0)

    run_dir = tmp_path / "runs" / f"20261006T093000Z-scripted-s7-{MACHINE}"
    assert json.loads((run_dir / "result.json").read_text())["outcome"] == "error"
