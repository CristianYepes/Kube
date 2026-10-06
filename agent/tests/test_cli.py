import json

import pytest

from kube_agent import cli
from kube_agent.bridge import BridgeError
from kube_agent.cli import build_parser, main
from kube_agent.config import DEFAULT_MAP

SUBCOMMANDS = ["run", "eval", "spend", "latency", "order-check"]
STUBS = ["eval", "latency", "order-check"]  # `run` is real since T5c and `spend` since T6


@pytest.fixture(autouse=True)
def no_episode_by_accident(monkeypatch):
    """A CLI test that reaches run_episode would start a real game and write into agent/runs/.

    This happened once: with `--seed` made optional on purpose, a test that expected argparse
    to refuse started a real episode and left a run folder in the repository. Tests that want
    run_episode replace it themselves, after this fixture.
    """
    async def refuse(*args, **kwargs):
        raise AssertionError("a CLI test reached run_episode: it would start a real episode")

    monkeypatch.setattr(cli, "run_episode", refuse)


def test_help_lists_every_subcommand(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    help_text = capsys.readouterr().out
    for name in SUBCOMMANDS:
        assert name in help_text


@pytest.mark.parametrize("name", STUBS)
def test_a_stub_says_so_and_fails(name, capsys):
    # A skeleton must never look like a success: exit code 1, message on stderr.
    assert main([name]) == 1
    assert f"kube-agent {name}: not implemented yet" in capsys.readouterr().err


def test_no_subcommand_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main([])

    assert exit_info.value.code == 2


def test_eval_takes_the_map_option():
    assert build_parser().parse_args(["eval"]).map == DEFAULT_MAP
    assert build_parser().parse_args(["eval", "--map", "x.cub"]).map == "x.cub"


def test_run_defaults():
    args = build_parser().parse_args(["run", "--policy", "idle", "--seed", "3"])

    assert (args.policy, args.seed, args.map, args.runner, args.max_seconds) == (
        "idle", 3, DEFAULT_MAP, "docker", 180.0)


@pytest.mark.parametrize("argv", [
    ["run", "--seed", "1"],  # no policy
    ["run", "--policy", "idle"],  # no seed
    ["run", "--policy", "jev", "--seed", "1"],  # not available until it exists
    ["run", "--policy", "idle", "--seed", "1", "--runner", "podman"],
])
def test_run_refuses_a_missing_or_unknown_option(argv, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(argv)

    assert exit_info.value.code == 2


def test_run_prints_the_summary_of_the_episode(monkeypatch, capsys):
    calls = []

    async def fake_run_episode(*args, **kwargs):
        calls.append((args, kwargs))
        return {
            "run_id": "20261006T000000Z-idle-s3-darwin", "policy": "idle", "seed": 3,
            "outcome": "lose", "survival_seconds": 9.87, "wave_reached": 1, "kills": 0,
            "decisions": 0, "decisions_applied": 0, "spend_usd": 0.0,
        }

    monkeypatch.setattr(cli, "run_episode", fake_run_episode)

    code = main(["run", "--policy", "idle", "--seed", "3", "--runner", "local", "--max-seconds", "30"])

    assert code == 0
    assert calls == [(("idle", 3, DEFAULT_MAP, "local", 30.0), {})]
    assert capsys.readouterr().out == (
        "idle s3: lose after 9.9 s (wave 1, 0 kills), 0 decisions, 0 applied, "
        "spend $0.0000  [20261006T000000Z-idle-s3-darwin]\n")


@pytest.mark.parametrize("error", [BridgeError("the game is gone"), FileNotFoundError("no such map")])
def test_run_reports_a_failed_episode_and_exits_1(monkeypatch, capsys, error):
    async def failing_run_episode(*args, **kwargs):
        raise error

    monkeypatch.setattr(cli, "run_episode", failing_run_episode)

    assert main(["run", "--policy", "idle", "--seed", "3"]) == 1
    assert str(error) in capsys.readouterr().err


# --- spend (T6) ---------------------------------------------------------------------------------


def write_decisions(folder, costs):
    folder.mkdir(parents=True)
    (folder / "decisions.jsonl").write_text("".join(json.dumps({"cost": cost}) + "\n" for cost in costs))


def test_spend_prints_the_total_and_what_is_left(monkeypatch, tmp_path, capsys):
    write_decisions(tmp_path / "run-a", [0.000054, 0.000054])
    write_decisions(tmp_path / "latency-b", [0.000042])
    monkeypatch.setattr(cli, "RUNS_DIR", tmp_path)

    code = main(["spend"])

    assert code == 0
    assert capsys.readouterr().out == (
        "spend: $0.000150 of $1.00 used, $0.999850 left (paid calls: 3, decisions files read: 2)\n")


def test_spend_on_an_empty_ledger_says_everything_is_left(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli, "RUNS_DIR", tmp_path)

    assert main(["spend"]) == 0
    assert capsys.readouterr().out == (
        "spend: $0.000000 of $1.00 used, $1.000000 left (paid calls: 0, decisions files read: 0)\n")


def test_spend_says_so_when_the_budget_is_spent(monkeypatch, tmp_path, capsys):
    write_decisions(tmp_path / "run-a", [1.0])
    monkeypatch.setattr(cli, "RUNS_DIR", tmp_path)

    assert main(["spend"]) == 0
    assert "the budget is spent: no more calls to Jev" in capsys.readouterr().out


def test_spend_stops_on_a_row_it_cannot_read(monkeypatch, tmp_path, capsys):
    (tmp_path / "run-a").mkdir()
    (tmp_path / "run-a" / "decisions.jsonl").write_text("this is not json\n")
    monkeypatch.setattr(cli, "RUNS_DIR", tmp_path)

    assert main(["spend"]) == 1
    assert "decisions.jsonl:1" in capsys.readouterr().err
