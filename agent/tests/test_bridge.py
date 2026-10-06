import asyncio
import json
import sys
from pathlib import Path

import pytest

from kube_agent.bridge import BridgeError, GameBridge, game_command

TESTS = Path(__file__).resolve().parent
FIXTURE = TESTS / "fixtures" / "idle_seed7.jsonl"
FAKE_GAME = TESTS / "fake_game.py"
RECORDED = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
GUARD_SECONDS = 20  # a bridge that hangs must fail the test, not freeze pytest


def run(coroutine):
    return asyncio.run(asyncio.wait_for(coroutine, GUARD_SECONDS))


def fake(tmp_path, mode="normal", **options):
    echo = tmp_path / "stdin_seen.txt"
    command = [sys.executable, str(FAKE_GAME), str(FIXTURE), str(echo), mode]
    return GameBridge(command, cwd=tmp_path, **options), echo


async def read_all(game):
    """Everything until the game's output ends: only for a game that exits by itself."""
    return [obs async for obs in game.observations()]


async def read_some(game, count):
    """The game keeps its output open until it reads Q, so a live game is read by count."""
    observations = []
    async for obs in game.observations():
        observations.append(obs)
        if len(observations) == count:
            break
    return observations


def test_init_message_is_parsed(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path)
        async with game:
            return game.init

    init = run(scenario())

    assert init == RECORDED[0]
    assert (init["type"], init["seed"], init["width"], init["height"]) == ("init", 7, 33, 14)


def test_every_observation_arrives_in_order(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path)
        async with game:
            return await read_some(game, len(RECORDED) - 1)

    observations = run(scenario())

    assert observations == RECORDED[1:]
    assert [obs["frame"] for obs in observations] == list(range(1, len(RECORDED)))


def test_commands_arrive_in_order_and_close_sends_q(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path)
        async with game:
            await game.send("C 1 0 0 0 0 0 0")
            await game.send("C 0 0 0 0 1 0 0")
            await game.send("C 0 0 0 0 0 0 1")

    run(scenario())

    echo = tmp_path / "stdin_seen.txt"
    assert echo.read_text().splitlines() == ["C 1 0 0 0 0 0 0", "C 0 0 0 0 1 0 0", "C 0 0 0 0 0 0 1", "Q"]


def test_close_after_a_clean_exit_does_not_raise(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path)
        await game.start()
        await game.close()
        return game.returncode

    assert run(scenario()) == 0


def test_close_works_with_most_observations_unread(tmp_path):
    # The fixture is 155 KB, more than a pipe holds. If close() did not read what the game
    # still prints, the child would block on its write and never see Q.
    async def scenario():
        game, _ = fake(tmp_path)
        async with game:
            seen = [await anext(game.observations()) for _ in range(3)]
        return seen

    assert len(run(scenario())) == 3


def test_the_child_runs_in_the_given_directory(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path)
        async with game:
            pass

    run(scenario())

    assert Path((tmp_path / "stdin_seen.txt.cwd").read_text()) == tmp_path.resolve()


def test_a_game_that_dies_before_init_is_reported_with_its_stderr(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path, "no-output")
        await game.start()

    with pytest.raises(BridgeError) as error:
        run(scenario())

    message = str(error.value)
    assert "exited with code 1 before its init line" in message
    assert "boom" in message
    assert "fake_game.py" in message


def test_a_game_that_never_prints_init_is_terminated_and_reported(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path, "hang", start_timeout=0.3)
        with pytest.raises(BridgeError) as error:
            await game.start()
        return game, error

    game, error = run(scenario())

    assert "no init line within 0.3 s" in str(error.value)
    assert game.returncode is not None


def test_a_line_that_is_not_json_is_reported_and_the_game_is_terminated(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path, "garbage")
        with pytest.raises(BridgeError) as error:
            await game.start()
        return game, error

    game, error = run(scenario())

    assert "not JSON" in str(error.value)
    assert "this is not json" in str(error.value)
    assert game.returncode is not None  # a failed start must not leave a game running


def test_a_json_line_that_is_not_an_object_is_reported(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path, "not-object")
        await game.start()

    with pytest.raises(BridgeError, match="not a JSON object"):
        run(scenario())


def test_a_first_line_that_is_not_init_is_reported_and_the_game_is_terminated(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path, "not-init")
        with pytest.raises(BridgeError) as error:
            await game.start()
        return game, error

    game, error = run(scenario())

    assert "expected an init line" in str(error.value)
    assert game.returncode is not None


def test_a_line_of_an_unknown_type_after_init_is_reported(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path, "bad-type")
        async with game:
            await read_all(game)

    with pytest.raises(BridgeError, match="expected an obs line, got type 'weird'"):
        run(scenario())


def test_a_game_that_crashes_after_init_fails_at_close(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path, "dies-after-init")
        await game.start()
        assert await read_all(game) == []
        await game.close()

    with pytest.raises(BridgeError) as error:
        run(scenario())

    assert "exited with code 3" in str(error.value)
    assert "crashed" in str(error.value)


def test_a_game_that_ignores_q_is_terminated_and_reported(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path, "stubborn", close_timeout=0.3)
        await game.start()
        with pytest.raises(BridgeError) as error:
            await game.close()
        return game, error

    game, error = run(scenario())

    assert "did not exit within 0.3 s after Q" in str(error.value)
    assert game.returncode is not None  # it was terminated, not left running


def test_send_after_the_game_exited_is_reported(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path, "dies-after-init")
        await game.start()
        await read_all(game)
        await game.send("C 0 0 0 0 0 0 0")

    with pytest.raises(BridgeError) as error:
        run(scenario())

    assert "could not send" in str(error.value)


def test_a_command_with_a_newline_is_refused_before_it_reaches_the_game(tmp_path):
    async def scenario():
        game, _ = fake(tmp_path)
        async with game:
            await game.send("C 1 0 0 0 0 0 0\nC 0 0 0 0 0 0 1")

    with pytest.raises(ValueError, match="newline"):
        run(scenario())


def test_game_command_docker():
    assert game_command("docker", "maps/x.cub", 7) == [
        "docker", "exec", "-i", "-e", "DISPLAY=:99", "-w", "/kube", "kube-dev",
        "./agent/cub3D_agent", "maps/x.cub", "7",
    ]


def test_game_command_local():
    assert game_command("local", "maps/x.cub", 7) == ["./agent/cub3D_agent", "maps/x.cub", "7"]


def test_game_command_rejects_an_unknown_runner():
    with pytest.raises(ValueError, match="'docker' or 'local'"):
        game_command("podman", "maps/x.cub", 7)
