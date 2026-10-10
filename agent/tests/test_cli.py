import json

import pytest

from kube_agent import cli, jev_client
from kube_agent.bridge import BridgeError
from kube_agent.cli import build_parser, main
from kube_agent.config import DEFAULT_MAP, DEFAULT_RUN_BUDGET_USD, EVAL_BUDGET_USD, LATENCY_PROBE_BUDGET_USD, ORDER_CHECK_BUDGET_USD
from kube_agent.evaluation import EvalRefused
from kube_agent.jev_client import BudgetExhausted, KeyMissing
from kube_agent.order_check import describe_order_check
from kube_agent.probes import describe_latency

SUBCOMMANDS = ["run", "eval", "spend", "latency", "order-check", "view"]


@pytest.fixture(autouse=True)
def no_episode_by_accident(monkeypatch):
    """A CLI test that reaches run_episode would start a real game and write into agent/runs/.

    This happened once: with `--seed` made optional on purpose, a test that expected argparse
    to refuse started a real episode and left a run folder in the repository. Tests that want
    run_episode replace it themselves, after this fixture.
    """
    async def refuse(*args, **kwargs):
        raise AssertionError("a CLI test reached run_episode: it would start a real episode")

    async def refuse_evaluation(*args, **kwargs):
        raise AssertionError("a CLI test reached run_evaluation: it would play a whole evaluation")

    def refuse_serving(*args, **kwargs):
        raise AssertionError("a CLI test reached serve: it would open a port and wait to be interrupted")

    monkeypatch.setattr(cli, "run_episode", refuse)
    monkeypatch.setattr(cli, "run_evaluation", refuse_evaluation)
    monkeypatch.setattr(cli, "serve", refuse_serving)


class FakeJev:
    """Stands in for JevClient in the CLI tests: from_environment never reaches the real one."""

    @classmethod
    def from_environment(cls, **kwargs):
        raise AssertionError("a CLI test reached the real JevClient.from_environment: it could spend money")


@pytest.fixture(autouse=True)
def no_spending_by_accident(monkeypatch):
    """A CLI test that reaches the real client could make a paid call if a key were in the environment."""
    monkeypatch.setattr(cli, "JevClient", FakeJev)


def test_help_lists_every_subcommand(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["--help"])

    assert exit_info.value.code == 0
    help_text = capsys.readouterr().out
    for name in SUBCOMMANDS:
        assert name in help_text


def test_no_subcommand_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main([])

    assert exit_info.value.code == 2


def test_run_defaults():
    args = build_parser().parse_args(["run", "--policy", "idle", "--seed", "3"])

    assert (args.policy, args.seed, args.map, args.runner, args.max_seconds, args.budget_usd) == (
        "idle", 3, DEFAULT_MAP, "docker", 180.0, DEFAULT_RUN_BUDGET_USD)


@pytest.mark.parametrize("argv", [
    ["run", "--seed", "1"],  # no policy
    ["run", "--policy", "idle"],  # no seed
    ["run", "--policy", "chess", "--seed", "1"],  # a policy that does not exist
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
    assert calls == [(("idle", 3, DEFAULT_MAP, "local", 30.0), {"budget_usd": DEFAULT_RUN_BUDGET_USD})]
    assert capsys.readouterr().out == (
        "idle s3: lose after 9.9 s (wave 1, 0 kills), 0 decisions, 0 applied, "
        "spend $0.0000  [20261006T000000Z-idle-s3-darwin]\n")


@pytest.mark.parametrize("error", [
    BridgeError("the game is gone"), FileNotFoundError("no such map"),
    KeyMissing("OPENROUTER_API_KEY is not set"), BudgetExhausted("the $1.00 total budget is spent"),
])
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


# --- latency (T6b) ------------------------------------------------------------------------------

LATENCY_RESULT = {
    "kind": "latency", "run_id": "latency-20261006T093000Z-darwin", "calls_requested": 50, "calls_made": 50,
    "ok": 50, "errors": 0, "models": {"typesafe/jev-1.13-20260917": 50},
    "latency_ms": {"p50": 120, "p95": 210, "min": 90, "max": 300, "mean": 135.5},
    "input_tokens_per_call": 1300.0, "cost_per_call_usd": 0.000055, "cost_sources": {"usage.cost": 50},
    "spend_usd": 0.00275, "stopped": None,
}


class AsyncNothing:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *exception_info):
        return None


def fake_probe(monkeypatch, result, calls=None):
    class Client(AsyncNothing):
        @classmethod
        def from_environment(cls, **kwargs):
            (calls if calls is not None else []).append(("from_environment", kwargs))
            return cls()

    async def run_latency(client, state, questions, n):
        (calls if calls is not None else []).append(("run_latency", n, sorted(questions)))
        return result

    monkeypatch.setattr(cli, "JevClient", Client)
    monkeypatch.setattr(cli, "run_latency", run_latency)


def test_latency_defaults_are_50_calls_and_a_small_cap():
    args = build_parser().parse_args(["latency"])

    assert (args.n, args.budget_usd) == (50, LATENCY_PROBE_BUDGET_USD)
    assert LATENCY_PROBE_BUDGET_USD == 0.01  # three times the estimate for 50 calls


@pytest.mark.parametrize("n", ["0", "-3", "x"])
def test_latency_needs_a_positive_number_of_calls(n, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["latency", "--n", n])

    assert exit_info.value.code == 2


def test_latency_prints_one_summary_line_and_exits_0(monkeypatch, capsys):
    calls = []
    fake_probe(monkeypatch, LATENCY_RESULT, calls)

    code = main(["latency", "--n", "50", "--budget-usd", "0.02"])

    assert code == 0
    assert calls == [("from_environment", {"cap_usd": 0.02}), ("run_latency", 50, ["tactic"])]
    assert capsys.readouterr().out == describe_latency(LATENCY_RESULT) + "\n"


def test_the_summary_line_has_the_numbers_r12_needs():
    assert describe_latency(LATENCY_RESULT) == (
        "latency: 50 calls (50 ok, 0 errors) | p50 120 ms, p95 210 ms, max 300 ms | "
        "1300 input tokens and $0.000055 per call | $0.002750 in all | cost from usage.cost | "
        "model typesafe/jev-1.13-20260917 | [latency-20261006T093000Z-darwin]")


def test_the_summary_line_when_no_call_was_answered():
    result = {**LATENCY_RESULT, "ok": 0, "errors": 3, "calls_made": 3, "latency_ms": None, "models": {},
              "cost_per_call_usd": None, "input_tokens_per_call": None, "cost_sources": {}, "spend_usd": 0.0}

    assert describe_latency(result) == (
        "latency: 3 calls (0 ok, 3 errors) | no call was answered | $0.000000 in all | [latency-20261006T093000Z-darwin]")


@pytest.mark.parametrize("error", [KeyMissing("OPENROUTER_API_KEY is not set"), BudgetExhausted("the $1.00 total budget is spent")])
def test_latency_refuses_to_start_without_a_key_or_a_budget(monkeypatch, capsys, error):
    class Client:
        @classmethod
        def from_environment(cls, **kwargs):
            raise error

    monkeypatch.setattr(cli, "JevClient", Client)

    assert main(["latency"]) == 1
    assert str(error) in capsys.readouterr().err


def test_an_unusable_key_is_reported_without_showing_it(monkeypatch, capsys):
    secret = "sk-or-v1-has a space-" + "ab12" * 8  # not printable ASCII without whitespace: the SDK refuses it
    monkeypatch.setattr(cli, "JevClient", jev_client.JevClient)
    monkeypatch.setenv("OPENROUTER_API_KEY", secret)

    assert main(["latency"]) == 1
    error = capsys.readouterr().err
    assert "kube-agent latency:" in error and secret not in error and "ab12ab12" not in error


def test_a_model_that_is_not_the_expected_one_exits_2_and_says_to_tell_the_owner(monkeypatch, capsys):
    stopped = "unexpected model: 'typesafe/jev-9' answered and 'typesafe/jev-1.13-20260917' was expected"
    fake_probe(monkeypatch, {**LATENCY_RESULT, "calls_made": 1, "ok": 1, "stopped": stopped})

    assert main(["latency"]) == 2
    assert "STOP" in capsys.readouterr().err


def test_any_other_early_stop_exits_1_with_the_reason(monkeypatch, capsys):
    fake_probe(monkeypatch, {**LATENCY_RESULT, "stopped": "budget cap reached: $0.010020 spent of the $0.010000 cap"})

    assert main(["latency"]) == 1
    assert "stopped early: budget cap reached" in capsys.readouterr().err


def test_run_with_the_jev_policy_passes_its_budget_on(monkeypatch, capsys):
    calls = []

    async def fake_run_episode(*args, **kwargs):
        calls.append((args, kwargs))
        return {
            "run_id": "20261006T000000Z-jev-s1-darwin", "policy": "jev", "seed": 1, "outcome": "win",
            "survival_seconds": 14.2, "wave_reached": 3, "kills": 8, "decisions": 29, "decisions_applied": 12,
            "spend_usd": 0.000905,
        }

    monkeypatch.setattr(cli, "run_episode", fake_run_episode)

    code = main(["run", "--policy", "jev", "--seed", "1", "--max-seconds", "60", "--budget-usd", "0.02"])

    assert code == 0
    assert calls == [(("jev", 1, DEFAULT_MAP, "docker", 60.0), {"budget_usd": 0.02})]
    assert "jev s1: win after 14.2 s (wave 3, 8 kills), 29 decisions, 12 applied, spend $0.0009" in capsys.readouterr().out


# --- order-check (T8) ---------------------------------------------------------------------------

ORDER_RESULT = {
    "kind": "order-check", "run_id": "order-check-20261008T093000Z-darwin", "calls_requested": 300, "calls_made": 0,
    "ok": 0, "errors": 0, "spend_usd": 0.0, "order": None, "stopped": None,
}


def fake_order_check(monkeypatch, result, calls=None, states=("state-a", "state-b")):
    record = (calls if calls is not None else []).append

    class Client(AsyncNothing):
        @classmethod
        def from_environment(cls, **kwargs):
            record(("from_environment", kwargs))
            return cls()

    def load_dev_states(runs_dir, n):
        record(("load_dev_states", n))
        return list(states)

    def load_states_of(runs_dir, folder, n):
        record(("load_states_of", folder, n))
        return list(states)

    async def run_order_check(client, picked, question):
        record(("run_order_check", picked, question["type"]))
        return result

    monkeypatch.setattr(cli, "JevClient", Client)
    monkeypatch.setattr(cli, "load_dev_states", load_dev_states)
    monkeypatch.setattr(cli, "load_states_of", load_states_of)
    monkeypatch.setattr(cli, "run_order_check", run_order_check)


def test_order_check_defaults_are_100_states_and_a_cap_twice_the_estimate():
    args = build_parser().parse_args(["order-check"])

    assert (args.n, args.budget_usd) == (100, ORDER_CHECK_BUDGET_USD)
    assert ORDER_CHECK_BUDGET_USD == 0.02  # 300 calls of $0.0000312 are about $0.0094


@pytest.mark.parametrize("n", ["0", "-3", "x"])
def test_order_check_needs_a_positive_number_of_states(n):
    with pytest.raises(SystemExit) as exit_info:
        main(["order-check", "--n", n])

    assert exit_info.value.code == 2


def test_order_check_prints_one_summary_line_and_exits_0(monkeypatch, capsys):
    calls = []
    fake_order_check(monkeypatch, ORDER_RESULT, calls)

    code = main(["order-check", "--n", "7", "--budget-usd", "0.03"])

    assert code == 0
    assert calls == [("load_dev_states", 7), ("from_environment", {"cap_usd": 0.03}), ("run_order_check", ["state-a", "state-b"], "choice")]
    assert capsys.readouterr().out == describe_order_check(ORDER_RESULT) + "\n"


def test_order_check_can_reuse_the_states_of_an_earlier_check(monkeypatch, capsys):
    calls = []
    fake_order_check(monkeypatch, ORDER_RESULT, calls)

    code = main(["order-check", "--same-states-as", "order-check-20261008T085011Z-darwin", "--n", "7"])

    assert code == 0
    assert calls[0] == ("load_states_of", "order-check-20261008T085011Z-darwin", 7)  # and no new states were drawn
    assert [call[0] for call in calls] == ["load_states_of", "from_environment", "run_order_check"]


def test_order_check_with_too_few_logged_states_says_so_before_anything_is_paid(monkeypatch, capsys):
    calls = []
    fake_order_check(monkeypatch, ORDER_RESULT, calls)

    def too_few(runs_dir, n):
        raise ValueError("only 3 distinct states were logged on development seeds and 100 were asked")

    monkeypatch.setattr(cli, "load_dev_states", too_few)

    assert main(["order-check"]) == 1
    assert "only 3 distinct states" in capsys.readouterr().err
    assert calls == []  # no client was made


@pytest.mark.parametrize("error", [KeyMissing("OPENROUTER_API_KEY is not set"), BudgetExhausted("the $1.00 total budget is spent")])
def test_order_check_refuses_to_start_without_a_key_or_a_budget(monkeypatch, capsys, error):
    fake_order_check(monkeypatch, ORDER_RESULT)

    class Client:
        @classmethod
        def from_environment(cls, **kwargs):
            raise error

    monkeypatch.setattr(cli, "JevClient", Client)

    assert main(["order-check"]) == 1
    assert str(error) in capsys.readouterr().err


def test_order_check_with_a_model_that_is_not_the_expected_one_exits_2(monkeypatch, capsys):
    stopped = "unexpected model: 'typesafe/jev-9' answered and 'typesafe/jev-1.13-20260917' was expected"
    fake_order_check(monkeypatch, {**ORDER_RESULT, "stopped": stopped})

    assert main(["order-check"]) == 2
    assert "STOP, tell the owner" in capsys.readouterr().err


def test_order_check_stopped_early_for_any_other_reason_exits_1_with_it(monkeypatch, capsys):
    fake_order_check(monkeypatch, {**ORDER_RESULT, "stopped": "budget cap reached: $0.020020 spent of the $0.020000 cap"})

    assert main(["order-check"]) == 1
    assert "stopped early: budget cap reached" in capsys.readouterr().err


# --- eval (T9) ----------------------------------------------------------------------------------

EVAL_SUMMARY = {
    "kind": "eval", "run_id": "eval-20261009T080000Z-darwin", "episodes_planned": 120, "episodes_done": 120, "errors": 0,
    "spend_usd": 0.0412, "complete": True, "stopped": None,
}


def fake_evaluation(monkeypatch, summary=EVAL_SUMMARY, calls=None):
    async def run_evaluation(plan, **kwargs):
        (calls if calls is not None else []).append((plan, kwargs))
        return summary

    monkeypatch.setattr(cli, "run_evaluation", run_evaluation)


def test_eval_defaults_are_all_three_policies_the_default_map_and_a_cap_of_fifty_cents():
    args = build_parser().parse_args(["eval", "--seeds", "101-102"])

    assert args.seeds == [101, 102]
    assert args.policies == ["idle", "scripted", "jev"] and args.maps == [DEFAULT_MAP]
    assert (args.runner, args.max_seconds, args.budget_usd, args.per_episode_usd) == ("docker", 180.0, EVAL_BUDGET_USD, DEFAULT_RUN_BUDGET_USD)
    assert EVAL_BUDGET_USD == 0.50 and (args.repeat, args.resume) == (False, None)


def test_eval_passes_its_plan_on_and_prints_one_line(monkeypatch, capsys):
    calls = []
    fake_evaluation(monkeypatch, calls=calls)

    code = main(["eval", "--seeds", "101-103", "--maps", "a.cub,b.cub", "--policies", "scripted,jev", "--runner", "local",
                 "--max-seconds", "60", "--budget-usd", "0.2", "--per-episode-usd", "0.01"])

    assert code == 0
    assert calls == [({"seeds": [101, 102, 103], "maps": ["a.cub", "b.cub"], "policies": ["scripted", "jev"], "runner": "local",
                       "max_seconds": 60.0, "budget_usd": 0.2, "per_episode_usd": 0.01}, {"repeat": False, "resume": None})]
    out = capsys.readouterr().out
    assert "120 of 120" in out and "$0.0412" in out and "agent/runs/eval-20261009T080000Z-darwin/report.md" in out


def test_eval_needs_seeds_unless_it_resumes(monkeypatch, capsys):
    calls = []
    fake_evaluation(monkeypatch, calls=calls)

    assert main(["eval"]) == 1
    assert "--seeds" in capsys.readouterr().err and calls == []

    assert main(["eval", "--resume", "eval-20261009T080000Z-darwin"]) == 0
    assert calls == [(None, {"repeat": False, "resume": "eval-20261009T080000Z-darwin"})]  # the plan is read from that folder


def test_eval_can_be_told_to_measure_the_test_seeds_again(monkeypatch):
    calls = []
    fake_evaluation(monkeypatch, calls=calls)

    main(["eval", "--seeds", "101", "--repeat"])

    assert calls[0][1]["repeat"] is True


@pytest.mark.parametrize("argv", [["--seeds", "5-3"], ["--seeds", "1,1"], ["--seeds", "1", "--policies", "idle,wizard"], ["--seeds", "1", "--maps", ""]])
def test_eval_refuses_bad_options_before_anything_is_played(argv, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["eval", *argv])

    assert exit_info.value.code == 2


def test_eval_that_is_refused_says_why_and_exits_1(monkeypatch, capsys):
    async def refuse(plan, **kwargs):
        raise EvalRefused("the config in the code is not the frozen config")

    monkeypatch.setattr(cli, "run_evaluation", refuse)

    assert main(["eval", "--seeds", "101"]) == 1
    assert "kube-agent eval: the config in the code is not the frozen config" in capsys.readouterr().err


def test_an_evaluation_that_stopped_early_exits_1_and_says_how_to_resume(monkeypatch, capsys):
    fake_evaluation(monkeypatch, {**EVAL_SUMMARY, "episodes_done": 40, "complete": False, "stopped": "3 episodes failed in a row"})

    assert main(["eval", "--seeds", "101"]) == 1
    err = capsys.readouterr().err
    assert "INCOMPLETE" in err and "3 episodes failed in a row" in err and "--resume eval-20261009T080000Z-darwin" in err


# --- view (spec 003) ---------------------------------------------------------------------------------------------------------


def fake_serve(monkeypatch, code=0, error=None):
    calls = []

    def serve(*args, **kwargs):
        calls.append((args, kwargs))
        if error:
            raise error
        return code

    monkeypatch.setattr(cli, "serve", serve)
    return calls


def test_view_follows_the_live_run_on_port_8765_by_default(monkeypatch):
    calls = fake_serve(monkeypatch)

    assert main(["view"]) == 0
    assert calls == [((8765, None, None), {})]


def test_view_replays_a_folder_named_under_agent_runs(monkeypatch):
    calls = fake_serve(monkeypatch)
    name = "20261008T090926Z-jev-s12-darwin"

    assert main(["view", "--replay", name, "--until", "3.5", "--port", "9000"]) == 0
    assert calls == [((9000, cli.RUNS_DIR / name, 3.5), {})]


def test_view_replays_a_folder_given_as_a_path(monkeypatch, tmp_path):
    calls = fake_serve(monkeypatch)

    assert main(["view", "--replay", str(tmp_path)]) == 0
    assert calls == [((8765, tmp_path, None), {})]


def test_view_says_when_the_folder_to_replay_is_not_there(monkeypatch, capsys):
    calls = fake_serve(monkeypatch)

    assert main(["view", "--replay", "no-such-run"]) == 1
    assert "no run folder 'no-such-run'" in capsys.readouterr().err and calls == []


def test_view_until_needs_a_replay(monkeypatch, capsys):
    calls = fake_serve(monkeypatch)

    assert main(["view", "--until", "3"]) == 1
    assert "--until needs --replay" in capsys.readouterr().err and calls == []


@pytest.mark.parametrize("port", ["80", "1023", "65536", "abc", "-1", "8765.5"])
def test_view_refuses_a_port_that_is_not_one_of_the_user_ports(port, capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["view", "--port", port])

    assert exit_info.value.code == 2 and "port" in capsys.readouterr().err


@pytest.mark.parametrize("error", [ValueError("'x' is not the name of a run folder"), OSError(48, "cannot listen on 127.0.0.1:8765")])
def test_view_reports_what_could_not_start_and_exits_1(monkeypatch, capsys, error):
    fake_serve(monkeypatch, error=error)

    assert main(["view"]) == 1
    assert "kube-agent view: " in capsys.readouterr().err


def test_view_exits_with_the_code_of_the_server(monkeypatch):
    fake_serve(monkeypatch, code=1)

    assert main(["view"]) == 1
