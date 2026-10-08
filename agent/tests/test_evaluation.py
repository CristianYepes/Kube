"""The final evaluation (T9, AC11): `kube-agent eval` plays idle, scripted and Jev on the test seeds, once.

The episodes themselves are played by run_episode, which has its own tests; here it is replaced by a fake, so
nothing starts a game or calls Jev. What is tested is what eval adds: the order of the episodes, the refusal to
start with a config that is not the frozen one, the refusal to measure a test seed twice, the resuming, the
stops, and the numbers and the text of the report.
"""

import asyncio
import json
import platform
from datetime import datetime, timedelta, timezone

import pytest

from kube_agent import config
from kube_agent.evaluation import (
    EvalRefused,
    build_report,
    check_frozen,
    group_stats,
    jev_against_scripted,
    load_episodes,
    parse_seeds,
    plan_episodes,
    refuse_repeated_test_seeds,
    run_evaluation,
    stuck_seconds,
)
from kube_agent.ledger import read_ledger

FIXED = datetime(2026, 10, 9, 8, 0, 0, tzinfo=timezone.utc)
MACHINE = platform.system().lower()
HASH = config.config_sha256()
MAPS = ["maps/bonus/subject_map.cub", "agent/maps/pillars.cub"]


def run(coroutine):
    return asyncio.run(asyncio.wait_for(coroutine, 20))


# --- reading the seeds and planning the episodes -------------------------------------------------


@pytest.mark.parametrize("text, expected", [
    ("101-103", [101, 102, 103]),
    ("5", [5]),
    ("1,3,7", [1, 3, 7]),
    ("1-3,7,9-10", [1, 2, 3, 7, 9, 10]),
    ("3-3", [3]),
    (" 4 - 5 , 8 ", [4, 5, 8]),
])
def test_seeds_are_read_as_ranges_and_lists(text, expected):
    assert parse_seeds(text) == expected


@pytest.mark.parametrize("text", ["", "x", "5-3", "0", "-4", "1-", "1,,2", "1.5", "101-", "1-2-3"])
def test_seeds_that_make_no_sense_are_refused(text):
    with pytest.raises(ValueError, match="seed"):
        parse_seeds(text)


def test_a_seed_named_twice_is_refused():
    with pytest.raises(ValueError, match="twice"):
        parse_seeds("1-3,2")


def test_the_episodes_are_interleaved_seed_by_seed_then_map_then_policy():
    plan = plan_episodes([1, 2], ["m1", "m2"], ["idle", "scripted", "jev"])

    assert plan == [
        (1, "m1", "idle"), (1, "m1", "scripted"), (1, "m1", "jev"),
        (1, "m2", "idle"), (1, "m2", "scripted"), (1, "m2", "jev"),
        (2, "m1", "idle"), (2, "m1", "scripted"), (2, "m1", "jev"),
        (2, "m2", "idle"), (2, "m2", "scripted"), (2, "m2", "jev"),
    ]


# --- the frozen config ---------------------------------------------------------------------------


def write_frozen(path, sha):
    path.write_text(json.dumps({"config_sha256": sha}))
    return path


def test_the_frozen_hash_is_returned_when_it_is_the_current_one(tmp_path):
    assert check_frozen(write_frozen(tmp_path / "frozen.json", HASH)) == HASH


def test_a_config_that_is_not_the_frozen_one_is_refused(tmp_path):
    with pytest.raises(EvalRefused, match="not the frozen config"):
        check_frozen(write_frozen(tmp_path / "frozen.json", "0" * 64))


def test_without_a_frozen_file_nothing_is_evaluated(tmp_path):
    with pytest.raises(EvalRefused, match="no frozen config"):
        check_frozen(tmp_path / "frozen.json")


def test_the_real_frozen_file_matches_the_code():
    assert check_frozen() == HASH


# --- test seeds are measured once ----------------------------------------------------------------


def write_episode(folder, policy="scripted", seed=101, map_path=MAPS[0], outcome="win", survival=12.0, wave=3, damage=0,
                  stalls=0, tactic_seconds=None, spend=0.0, decisions=None, positions=None, kills=8):
    """An episode folder as run_episode leaves it, with only what the evaluation reads."""
    folder.mkdir(parents=True)
    result = {
        "run_id": folder.name, "policy": policy, "seed": seed, "map": map_path, "machine": MACHINE, "runner": "docker",
        "config_sha256": HASH, "max_seconds": 180.0, "outcome": outcome, "survival_seconds": survival,
        "wave_reached": wave, "kills": kills, "damage_taken": damage, "drops": 0, "stalls": stalls,
        "tactic_seconds": tactic_seconds if tactic_seconds is not None else {}, "switches": 2, "decisions": len(decisions or []),
        "decisions_applied": 0, "spend_usd": spend,
    }
    (folder / "result.json").write_text(json.dumps(result))
    (folder / "decisions.jsonl").write_text("".join(json.dumps(row) + "\n" for row in decisions or []))
    rows = positions if positions is not None else [{"t": 0.0, "x": 1.0, "y": 1.0, "hp": 100, "wave": 1, "enemies": 3, "tactic": "ENGAGE"}]
    (folder / "episode.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_a_test_seed_already_measured_is_refused(tmp_path):
    write_episode(tmp_path / "eval-old" / "ep1", policy="jev", seed=105, map_path=MAPS[1])

    with pytest.raises(EvalRefused, match="seed 105.*already measured.*eval-old"):
        refuse_repeated_test_seeds(tmp_path, plan_episodes([105], MAPS[1:], ["jev"]))


def test_another_policy_map_or_seed_is_not_a_repeat(tmp_path):
    write_episode(tmp_path / "eval-old" / "ep1", policy="jev", seed=105, map_path=MAPS[1])

    refuse_repeated_test_seeds(tmp_path, plan_episodes([105], MAPS[:1], ["jev"]))  # another map
    refuse_repeated_test_seeds(tmp_path, plan_episodes([105], MAPS[1:], ["scripted"]))  # another policy
    refuse_repeated_test_seeds(tmp_path, plan_episodes([106], MAPS[1:], ["jev"]))  # another seed


def test_development_seeds_may_be_evaluated_again(tmp_path):
    write_episode(tmp_path / "eval-old" / "ep1", policy="jev", seed=5, map_path=MAPS[1])

    refuse_repeated_test_seeds(tmp_path, plan_episodes([5], MAPS[1:], ["jev"]))


def test_an_episode_that_failed_does_not_count_as_measured(tmp_path):
    write_episode(tmp_path / "eval-old" / "ep1", policy="jev", seed=105, map_path=MAPS[1], outcome="error")

    refuse_repeated_test_seeds(tmp_path, plan_episodes([105], MAPS[1:], ["jev"]))


# --- running the evaluation ----------------------------------------------------------------------


class FakeEpisodes:
    """Stands in for run_episode: leaves a folder like the real one and returns its result."""

    def __init__(self, outcomes=None, spend=0.0004, fail_on=None):
        self.calls, self.outcomes, self.spend, self.fail_on = [], outcomes or {}, spend, fail_on or set()

    async def __call__(self, policy, seed, map_path, runner, max_seconds, runs_dir, budget_usd, **unused):
        self.calls.append({"policy": policy, "seed": seed, "map": map_path, "runner": runner, "max_seconds": max_seconds,
                           "runs_dir": runs_dir, "budget_usd": budget_usd, "ledger_dir": unused.get("ledger_dir")})
        folder = runs_dir / f"{len(self.calls):04d}-{policy}-s{seed}"
        outcome = "error" if (policy, seed, map_path) in self.fail_on else self.outcomes.get((policy, seed, map_path), "win")
        spend = self.spend if policy == "jev" else 0.0
        write_episode(folder, policy=policy, seed=seed, map_path=map_path, outcome=outcome, spend=spend,
                      survival=10.0 + seed % 7, decisions=[{"cost": spend, "latency_ms": 300, "error": None}] if policy == "jev" else [])
        return json.loads((folder / "result.json").read_text())


def plan(seeds=(101, 102), maps=tuple(MAPS), policies=("idle", "scripted", "jev"), **overrides):
    return {"seeds": list(seeds), "maps": list(maps), "policies": list(policies), "runner": "docker", "max_seconds": 180.0,
            "budget_usd": 0.50, "per_episode_usd": 0.05, **overrides}


def evaluate(tmp_path, fake=None, plan_=None, frozen=None, now=FIXED, **options):
    fake = fake or FakeEpisodes()
    frozen = frozen or write_frozen(tmp_path / "frozen.json", HASH)
    lines = []
    summary = run(run_evaluation(plan_ or plan(), runs_dir=tmp_path / "runs", run_episode=fake, utc_now=lambda: now,
                                 say=lines.append, frozen_path=frozen, **options))
    return summary, fake, lines


def test_every_planned_episode_is_played_in_the_interleaved_order(tmp_path):
    summary, fake, _ = evaluate(tmp_path, plan_=plan(seeds=[101, 102]))

    assert [(c["seed"], c["map"], c["policy"]) for c in fake.calls] == plan_episodes([101, 102], MAPS, ["idle", "scripted", "jev"])
    assert all(c["runner"] == "docker" and c["max_seconds"] == 180.0 for c in fake.calls)
    assert summary["episodes_done"] == 12 and summary["complete"] is True and summary["stopped"] is None


def test_the_folder_is_named_for_the_evaluation_the_time_and_the_machine_and_holds_the_episodes(tmp_path):
    summary, fake, _ = evaluate(tmp_path, plan_=plan(seeds=[101]))

    folder = tmp_path / "runs" / f"eval-20261009T080000Z-{MACHINE}"
    assert summary["run_id"] == folder.name
    assert all(c["runs_dir"] == folder for c in fake.calls)  # the ledger reads every decisions.jsonl below agent/runs
    assert {"plan.json", "result.json", "report.md"} <= {p.name for p in folder.iterdir()}
    assert json.loads((folder / "plan.json").read_text())["seeds"] == [101]


def test_the_spend_of_the_whole_project_is_what_the_clients_read_not_just_this_evaluations(tmp_path):
    _, fake, _ = evaluate(tmp_path, plan_=plan(seeds=[101], policies=["jev"], maps=MAPS[:1]))

    assert [c["ledger_dir"] for c in fake.calls] == [tmp_path / "runs"]  # agent/runs, not agent/runs/eval-...


def test_the_ledger_counts_the_evaluations_spend_once(tmp_path):
    summary, _, _ = evaluate(tmp_path, plan_=plan(seeds=[101, 102, 103]))

    ledger = read_ledger(tmp_path / "runs")

    assert ledger.spent == pytest.approx(6 * 0.0004) and ledger.paid_calls == 6  # 3 seeds x 2 maps of Jev
    assert summary["spend_usd"] == pytest.approx(ledger.spent)


def test_the_cap_of_one_jev_episode_is_the_smaller_of_its_own_and_what_is_left(tmp_path):
    _, fake, _ = evaluate(tmp_path, plan_=plan(seeds=[101, 102], budget_usd=0.0009, per_episode_usd=0.05, policies=["jev"], maps=MAPS[:1]))

    assert [round(c["budget_usd"], 4) for c in fake.calls] == [0.0009, 0.0005]


def test_when_the_evaluation_budget_is_spent_it_stops_and_says_so(tmp_path):
    summary, fake, _ = evaluate(tmp_path, plan_=plan(seeds=[101, 102, 103], budget_usd=0.0007, policies=["jev"], maps=MAPS[:1]))

    assert len(fake.calls) == 2  # the second one reaches the cap
    assert summary["stopped"].startswith("budget") and summary["complete"] is False
    assert "INCOMPLETE" in (tmp_path / "runs" / summary["run_id"] / "report.md").read_text()


def test_three_failed_episodes_in_a_row_stop_it(tmp_path):
    failing = {(p, s, m) for s in (101, 102) for m in MAPS for p in ("idle", "scripted", "jev")}
    summary, fake, _ = evaluate(tmp_path, fake=FakeEpisodes(fail_on=failing), plan_=plan(seeds=[101, 102]))

    assert len(fake.calls) == 3 and summary["stopped"].startswith("3 episodes failed in a row")


def test_a_failed_episode_that_is_followed_by_a_good_one_does_not_stop_it(tmp_path):
    summary, fake, _ = evaluate(tmp_path, fake=FakeEpisodes(fail_on={("idle", 101, MAPS[0])}), plan_=plan(seeds=[101]))

    assert len(fake.calls) == 6 and summary["stopped"] is None
    assert summary["complete"] is False and summary["errors"] == 1  # one episode has no result, so it is not complete


def test_one_line_of_progress_per_episode(tmp_path):
    _, _, lines = evaluate(tmp_path, plan_=plan(seeds=[101], policies=["scripted"], maps=MAPS[:1]))

    assert len(lines) >= 1 and any("scripted" in line and "101" in line for line in lines)


def test_an_evaluation_with_another_config_never_starts(tmp_path):
    frozen = write_frozen(tmp_path / "other.json", "0" * 64)

    with pytest.raises(EvalRefused):
        evaluate(tmp_path, frozen=frozen)

    assert not (tmp_path / "runs").exists() or not list((tmp_path / "runs").iterdir())


def test_a_second_evaluation_of_the_same_test_seeds_is_refused_unless_it_is_asked_for(tmp_path):
    evaluate(tmp_path, plan_=plan(seeds=[101], policies=["scripted"], maps=MAPS[:1]))

    with pytest.raises(EvalRefused, match="already measured"):
        evaluate(tmp_path, plan_=plan(seeds=[101], policies=["scripted"], maps=MAPS[:1]))
    summary, _, _ = evaluate(tmp_path, plan_=plan(seeds=[101], policies=["scripted"], maps=MAPS[:1]), repeat=True,
                           now=FIXED + timedelta(hours=1))
    assert summary["episodes_done"] == 1


def test_resuming_plays_only_what_is_missing_in_the_same_folder(tmp_path):
    failing = FakeEpisodes(fail_on={("jev", 102, MAPS[1]), ("scripted", 102, MAPS[1]), ("idle", 102, MAPS[1])})
    first, _, _ = evaluate(tmp_path, fake=failing, plan_=plan(seeds=[101, 102]))
    assert first["complete"] is False

    second, fake, _ = evaluate(tmp_path, plan_=plan(seeds=[101, 102]), resume=first["run_id"])

    assert second["run_id"] == first["run_id"]
    assert [(c["seed"], c["map"], c["policy"]) for c in fake.calls] == [(102, MAPS[1], p) for p in ("idle", "scripted", "jev")]
    assert second["complete"] is True and second["episodes_done"] == 12


def test_resuming_a_folder_that_does_not_exist_is_refused(tmp_path):
    with pytest.raises(EvalRefused, match="eval-nope"):
        evaluate(tmp_path, resume="eval-nope")


def test_the_budget_stops_the_evaluation_exactly_when_it_is_spent_not_one_episode_later(tmp_path):
    summary, fake, _ = evaluate(tmp_path, plan_=plan(seeds=[101, 102], budget_usd=0.0004, policies=["jev"], maps=MAPS[:1]))

    assert len(fake.calls) == 1 and summary["stopped"].startswith("budget")


def test_failed_episodes_that_are_not_in_a_row_never_stop_it_however_many_there_are(tmp_path):
    failing = {("idle", 101, MAPS[0]), ("jev", 101, MAPS[0]), ("scripted", 101, MAPS[1])}  # fail, ok, fail, ok, fail, ok
    summary, fake, _ = evaluate(tmp_path, fake=FakeEpisodes(fail_on=failing), plan_=plan(seeds=[101]))

    assert len(fake.calls) == 6 and summary["stopped"] is None and summary["errors"] == 3


def test_an_exception_of_an_episode_stops_the_evaluation_but_what_was_played_is_reported(tmp_path):
    class Breaks(FakeEpisodes):
        async def __call__(self, policy, seed, map_path, runner, max_seconds, runs_dir, budget_usd, **unused):
            if len(self.calls) == 2:
                raise RuntimeError("OPENROUTER_API_KEY is not set")
            return await super().__call__(policy, seed, map_path, runner, max_seconds, runs_dir, budget_usd)

    summary, fake, _ = evaluate(tmp_path, fake=Breaks(), plan_=plan(seeds=[101]))

    assert summary["stopped"] == "RuntimeError: OPENROUTER_API_KEY is not set" and summary["episodes_done"] == 2
    assert "INCOMPLETE" in (tmp_path / "runs" / summary["run_id"] / "report.md").read_text()


def test_an_evaluation_folder_is_never_overwritten(tmp_path):
    evaluate(tmp_path, plan_=plan(seeds=[101], policies=["scripted"], maps=MAPS[:1]))

    with pytest.raises(FileExistsError):
        evaluate(tmp_path, plan_=plan(seeds=[101], policies=["scripted"], maps=MAPS[:1]), repeat=True)  # the same second


def test_a_map_that_does_not_exist_is_refused_before_anything_is_played(tmp_path):
    with pytest.raises(EvalRefused, match="map not found: agent/maps/nope.cub"):
        evaluate(tmp_path, plan_=plan(maps=["agent/maps/nope.cub"]))

    assert not (tmp_path / "runs").exists()


# --- Jev against scripted ------------------------------------------------------------------------


def pair(jev_times, scripted_times, jev_outcomes=None):
    eps = []
    for seed, (j, s) in enumerate(zip(jev_times, scripted_times), start=101):
        eps.append(episode(policy="jev", survival=j, seed=seed, outcome=(jev_outcomes or {}).get(seed, "win")))
        eps.append(episode(policy="scripted", survival=s, seed=seed))
    return eps


def test_the_difference_in_time_to_win_is_taken_seed_by_seed_where_both_won():
    result = jev_against_scripted(pair([13.0, 12.0, 20.0, 9.0], [12.0, 12.0, 18.0, 10.0]))

    assert (result["seeds"], result["both_won"]) == (4, 4)
    assert (result["faster"], result["slower"], result["equal"]) == (1, 2, 1)
    assert result["median_difference"] == pytest.approx(0.5) and result["mean_difference"] == pytest.approx(0.5)


def test_a_seed_that_jev_did_not_win_is_not_in_the_time_difference():
    result = jev_against_scripted(pair([13.0, 180.0], [12.0, 12.0], jev_outcomes={102: "timeout"}))

    assert (result["seeds"], result["both_won"]) == (2, 1)
    assert result["median_difference"] == pytest.approx(1.0)


def test_the_sign_test_is_exact_and_two_sided():
    all_slower = jev_against_scripted(pair([13.0] * 4, [12.0] * 4))
    fifteen_of_twenty = jev_against_scripted(pair([13.0] * 15 + [11.0] * 5, [12.0] * 20))
    even = jev_against_scripted(pair([13.0, 11.0], [12.0, 12.0]))

    assert all_slower["sign_test_p"] == pytest.approx(0.125)  # 2 * 1/16
    assert fifteen_of_twenty["sign_test_p"] == pytest.approx(0.0414, abs=1e-4)  # the pillars result of R16
    assert even["sign_test_p"] == 1.0


def test_with_no_seed_in_common_there_is_no_comparison():
    assert jev_against_scripted([episode(policy="jev", seed=101), episode(policy="scripted", seed=102)]) is None


# --- the numbers of the report -------------------------------------------------------------------


def episode(policy="scripted", outcome="win", survival=12.0, wave=3, damage=0, tactic_seconds=None, spend=0.0, decisions=None, positions=None, seed=101, stalls=0):
    return {
        "result": {"run_id": f"{policy}-{seed}", "policy": policy, "seed": seed, "map": MAPS[0], "outcome": outcome, "survival_seconds": survival,
                   "wave_reached": wave, "damage_taken": damage, "stalls": stalls, "drops": 0, "tactic_seconds": tactic_seconds or {}, "spend_usd": spend},
        "decisions": decisions or [], "episode": positions or [],
    }


def test_wins_have_a_wilson_interval_and_every_outcome_is_counted():
    stats = group_stats([episode(), episode(), episode(), episode(outcome="lose", survival=8.0, wave=2), episode(outcome="timeout", survival=180.0, wave=2)])

    assert stats["n"] == 5 and stats["outcomes"] == {"win": 3, "lose": 1, "timeout": 1}
    assert stats["wins"] == 3 and stats["wins_wilson95"] == pytest.approx([0.2307, 0.8825], abs=1e-3)


def test_survival_and_time_to_win_have_median_and_quartiles():
    times = [10.0, 11.0, 12.0, 13.0, 14.0]
    stats = group_stats([episode(survival=t) for t in times] + [episode(outcome="lose", survival=4.0, wave=1)])

    assert stats["survival"] == {"median": 11.5, "q1": 10.25, "q3": 12.75}  # the 6 values 4, 10, 11, 12, 13, 14
    assert stats["time_to_win"] == {"median": 12.0, "q1": 11.0, "q3": 13.0}


def test_with_no_win_there_is_no_time_to_win():
    stats = group_stats([episode(outcome="lose", survival=7.0, wave=1)])

    assert stats["time_to_win"] is None and stats["wins"] == 0


def test_waves_cleared_count_all_three_for_a_win_and_the_ones_before_the_last_for_the_others():
    stats = group_stats([episode(), episode(outcome="lose", wave=2), episode(outcome="lose", wave=1)])

    assert stats["waves_cleared_mean"] == pytest.approx((3 + 1 + 0) / 3)


def test_damage_stalls_and_the_time_in_each_tactic_in_wins_losses_and_timeouts():
    stats = group_stats([
        episode(damage=10, stalls=1, tactic_seconds={"ENGAGE": 6.0, "KITE": 2.0}),
        episode(damage=0, stalls=2, tactic_seconds={"ENGAGE": 2.0}),
        episode(outcome="lose", damage=100, tactic_seconds={"RETREAT": 5.0, "ENGAGE": 5.0}),
        episode(outcome="timeout", survival=180.0, wave=2, tactic_seconds={"SEARCH": 170.0}),
    ])

    assert stats["damage"] == {"episodes": 2, "mean": pytest.approx(110 / 4)}
    assert stats["stalls"] == 3
    assert stats["tactic_share"]["win"] == pytest.approx({"ENGAGE": 0.8, "KITE": 0.2})
    assert stats["tactic_share"]["lose"] == pytest.approx({"RETREAT": 0.5, "ENGAGE": 0.5})
    assert stats["tactic_share"]["timeout"] == pytest.approx({"SEARCH": 1.0})


def test_idle_has_no_tactic_share():
    stats = group_stats([episode(policy="idle", outcome="lose", tactic_seconds={})])

    assert stats["tactic_share"] == {"win": {}, "lose": {}, "timeout": {}}


def test_failed_episodes_are_counted_apart_and_left_out_of_n():
    stats = group_stats([episode(), episode(outcome="error", survival=0.0)])

    assert stats["n"] == 1 and stats["errors"] == 1


def jev_rows(*latencies, cost=0.00003, reason=None, source="jev"):
    return [{"cost": cost, "latency_ms": ms, "error": None, "applied": reason is None, "reason": reason, "source": source} for ms in latencies]


def test_jev_has_cost_per_episode_latency_and_what_happened_to_its_answers():
    first = episode(policy="jev", spend=0.0009, decisions=jev_rows(100, 200, 300, 400) + jev_rows(500, reason="stale"))
    second = episode(policy="jev", spend=0.0011, decisions=jev_rows(1000, 600, reason="below_threshold"))
    errored = {"cost": 0.0, "latency_ms": 4001, "error": "TimeoutError: no answer within 4.0 s", "applied": False, "reason": "error", "source": "jev"}
    second["decisions"].append(errored)

    jev = group_stats([first, second])["jev"]

    assert jev["spend_per_episode"] == pytest.approx(0.001) and jev["spend_total"] == pytest.approx(0.002)
    assert jev["calls"] == 8 and jev["errors"] == 1
    assert jev["reasons"] == {"applied": 4, "stale": 1, "below_threshold": 2, "error": 1}
    assert jev["latency_ms"] == {"p50": 400, "p95": 1000, "max": 1000}  # the call that failed is not a latency


def test_an_episode_that_fell_back_to_the_rules_is_counted():
    fallback = episode(policy="jev", decisions=jev_rows(100) + jev_rows(0, source="scripted_fallback"))

    jev = group_stats([fallback, episode(policy="jev", decisions=jev_rows(100))])["jev"]

    assert jev["fallback_episodes"] == 1
    assert jev["calls"] == 2  # the row of the rules is not a call to Jev


def test_the_other_policies_have_no_jev_section():
    assert group_stats([episode(policy="scripted")])["jev"] is None


def test_a_timeout_that_changed_nothing_for_the_last_minute_is_marked_as_stuck():
    still = [{"t": float(t), "x": 25.9, "y": 12.7, "hp": 100, "wave": 2, "enemies": 4, "tactic": "SEARCH"} for t in range(0, 181, 1)]
    moving = [{"t": float(t), "x": 25.9 + (t % 5), "y": 12.7, "hp": 100, "wave": 2, "enemies": 4, "tactic": "SEARCH"} for t in range(0, 181, 1)]

    stats = group_stats([episode(outcome="timeout", survival=180.0, wave=2, positions=still), episode(outcome="timeout", survival=180.0, wave=2, positions=moving)])

    assert stats["outcomes"]["timeout"] == 2 and stats["stuck_timeouts"] == 1


def test_stuck_seconds_is_how_long_nothing_changed_at_the_end():
    rows = [{"t": 0.0, "x": 1.0, "y": 1.0, "enemies": 3}, {"t": 10.0, "x": 2.0, "y": 1.0, "enemies": 3}, {"t": 20.0, "x": 2.0, "y": 1.0, "enemies": 3},
            {"t": 90.0, "x": 2.0, "y": 1.0, "enemies": 3}]

    assert stuck_seconds(rows) == 80.0
    assert stuck_seconds(rows[:3] + [{"t": 95.0, "x": 2.0, "y": 1.0, "enemies": 2}]) == 0.0  # a kill is a change, with the player standing still
    assert stuck_seconds([]) == 0.0
    assert stuck_seconds(rows[:1]) == 0.0


# --- loading and the report ----------------------------------------------------------------------


def test_the_episodes_of_a_folder_are_loaded_with_their_decisions_and_path(tmp_path):
    write_episode(tmp_path / "ep1", policy="jev", seed=101, decisions=jev_rows(100))
    write_episode(tmp_path / "ep2", policy="idle", seed=101, outcome="lose")
    (tmp_path / "plan.json").write_text("{}")

    loaded = load_episodes(tmp_path)

    assert sorted(e["result"]["policy"] for e in loaded) == ["idle", "jev"]
    assert [e for e in loaded if e["result"]["policy"] == "jev"][0]["decisions"] == jev_rows(100)


def report_for(tmp_path, **kwargs):
    folder = tmp_path / "eval-x"
    for number, (policy, seed, map_path, outcome, survival) in enumerate([
        ("idle", 101, MAPS[0], "lose", 8.0), ("scripted", 101, MAPS[0], "win", 12.0), ("jev", 101, MAPS[0], "win", 12.5),
        ("idle", 101, MAPS[1], "lose", 11.0), ("scripted", 101, MAPS[1], "win", 19.0), ("jev", 101, MAPS[1], "win", 21.0),
    ]):
        write_episode(folder / f"ep{number}", policy=policy, seed=seed, map_path=map_path, outcome=outcome, survival=survival,
                      spend=0.0009 if policy == "jev" else 0.0, decisions=jev_rows(300, 350) if policy == "jev" else [],
                      tactic_seconds={"ENGAGE": 5.0, "KITE": 3.0} if policy != "idle" else {})
    plan_ = plan(seeds=[101], **kwargs)
    return build_report(load_episodes(folder), plan_, run_id="eval-x", frozen_sha=HASH, current_sha=HASH, stopped=None)


def test_the_report_prints_the_config_hash_and_says_that_it_is_the_frozen_one(tmp_path):
    text = report_for(tmp_path)

    assert HASH in text and "equals the frozen one" in text


def test_a_report_made_with_another_hash_says_so_loudly(tmp_path):
    folder = tmp_path / "eval-x"
    write_episode(folder / "ep", policy="scripted")

    text = build_report(load_episodes(folder), plan(seeds=[101]), run_id="eval-x", frozen_sha=HASH, current_sha="0" * 64, stopped=None)

    assert "DIFFERS from the frozen one" in text


def test_the_report_has_a_section_per_map_with_a_row_per_policy(tmp_path):
    text = report_for(tmp_path)

    for map_path in MAPS:
        assert f"## {map_path}" in text
    for policy in ("idle", "scripted", "jev"):
        assert f"| {policy} |" in text
    assert "Wilson" in text and "p50" in text and "per episode" in text


def test_the_report_compares_jev_with_scripted_on_the_same_seeds(tmp_path):
    text = report_for(tmp_path)

    assert "Jev against scripted" in text and "slower" in text


def test_an_incomplete_evaluation_is_marked_in_the_report(tmp_path):
    folder = tmp_path / "eval-x"
    write_episode(folder / "ep", policy="scripted")

    text = build_report(load_episodes(folder), plan(seeds=[101]), run_id="eval-x", frozen_sha=HASH, current_sha=HASH, stopped="budget of the evaluation spent")

    assert "INCOMPLETE" in text and "budget of the evaluation spent" in text


def test_each_map_has_its_own_numbers(tmp_path):
    text = report_for(tmp_path)
    first, second = [section for section in text.split("\n## ")[1:]]

    assert first.startswith(MAPS[0]) and second.startswith(MAPS[1])
    assert "12.0 [12.0-12.0]" in first and "19.0 [19.0-19.0]" not in first  # the time to win of scripted on each map
    assert "19.0 [19.0-19.0]" in second and "12.0 [12.0-12.0]" not in second
