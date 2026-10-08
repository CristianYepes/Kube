"""The option-order check of T8: does Jev's choice depend on the order the options are listed in?

jev-1.13 leans toward the first option of a Choice (R5), and ENGAGE is listed first. The check asks
each logged state three times: in the current order, in the opposite order, and in the current order
again. The third answer is the control: the same request does not always get the same answer (R12),
so some of the "differences" between the two orders are the model's noise and not the order.
"""

import asyncio
import json
import platform
from datetime import datetime, timezone

import pytest
from fake_jev import GUARD_SECONDS, FakeAPI, client_for, good

from kube_agent import config
from kube_agent.jev_client import EXPECTED_MODEL
from kube_agent.ledger import read_ledger
from kube_agent.order_check import (
    DEV_SEEDS,
    VARIANTS,
    describe_order_check,
    load_dev_states,
    order_requests,
    reversed_options,
    run_order_check,
    summarize_order_check,
)
from kube_agent.stats import wilson_interval

QUESTION = config.TACTIC_QUESTION
OPTIONS = list(QUESTION["criteria"])
E, K, R, S = OPTIONS
FIXED = datetime(2026, 10, 8, 9, 30, 0, tzinfo=timezone.utc)
MACHINE = platform.system().lower()


def run(coroutine):
    return asyncio.run(asyncio.wait_for(coroutine, GUARD_SECONDS))


def a_state(number):
    return {"threats": {"remaining": number}, "current_tactic": "ENGAGE"}


def numbers_of(picked):
    return sorted(item["state"]["threats"]["remaining"] for item in picked)


def make_run(runs_dir, name, policy, seed, numbers, source="jev", with_state=True):
    """A run folder as `kube-agent run` leaves it, with one decision row per number."""
    folder = runs_dir / name
    folder.mkdir(parents=True)
    (folder / "result.json").write_text(json.dumps({"run_id": name, "policy": policy, "seed": seed}))
    rows = []
    for number in numbers:
        row = {"t": number * 0.5, "tactic": "ENGAGE", "applied": True, "source": source}
        if with_state:
            row["state"] = a_state(number)
        rows.append(row)
    (folder / "decisions.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows))


# --- which states are asked ---------------------------------------------------------------------


def test_the_development_seeds_are_1_to_20():
    assert list(DEV_SEEDS) == list(range(1, 21))


def test_only_jev_episodes_on_development_seeds_are_used(tmp_path):
    make_run(tmp_path, "a-jev-s1", "jev", 1, [0, 1])
    make_run(tmp_path, "b-jev-s20", "jev", 20, [2, 3])
    make_run(tmp_path, "c-jev-s21", "jev", 21, [10])  # the first seed past the development ones
    make_run(tmp_path, "d-jev-s101", "jev", 101, [11])  # a test seed: never
    make_run(tmp_path, "e-jev-s0", "jev", 0, [12])  # just below the set
    make_run(tmp_path, "f-scripted-s3", "scripted", 3, [13])
    (tmp_path / "g-latency").mkdir()
    (tmp_path / "g-latency" / "result.json").write_text(json.dumps({"kind": "latency"}))

    assert numbers_of(load_dev_states(tmp_path, n=4)) == [0, 1, 2, 3]
    with pytest.raises(ValueError, match="only 4 distinct states"):  # so none of the others was in the pool
        load_dev_states(tmp_path, n=5)


def test_rows_that_are_not_jevs_answers_are_skipped(tmp_path):
    make_run(tmp_path, "a-jev-s1", "jev", 1, [0, 1])
    make_run(tmp_path, "b-jev-s2", "jev", 2, [5], source="scripted_fallback")
    make_run(tmp_path, "c-jev-s3", "jev", 3, [6], with_state=False)

    assert numbers_of(load_dev_states(tmp_path, n=2)) == [0, 1]
    with pytest.raises(ValueError, match="only 2 distinct states"):
        load_dev_states(tmp_path, n=3)


def test_a_state_logged_twice_counts_once(tmp_path):
    make_run(tmp_path, "a-jev-s1", "jev", 1, [0, 1, 2])
    make_run(tmp_path, "b-jev-s2", "jev", 2, [1, 2, 3])

    assert numbers_of(load_dev_states(tmp_path, n=4)) == [0, 1, 2, 3]
    with pytest.raises(ValueError, match="only 4 distinct states"):
        load_dev_states(tmp_path, n=5)


def test_the_sample_is_the_same_for_the_same_seed_and_differs_for_another(tmp_path):
    make_run(tmp_path, "a-jev-s1", "jev", 1, list(range(50)))

    first = load_dev_states(tmp_path, n=10, sample_seed=0)
    again = load_dev_states(tmp_path, n=10, sample_seed=0)
    other = load_dev_states(tmp_path, n=10, sample_seed=1)

    assert first == again
    assert first != other
    assert len({json.dumps(item["state"]) for item in first}) == 10


def test_each_state_remembers_the_run_and_the_row_it_came_from(tmp_path):
    make_run(tmp_path, "a-jev-s1", "jev", 1, [7, 8, 9])

    by_number = {item["state"]["threats"]["remaining"]: item for item in load_dev_states(tmp_path, n=3)}

    assert (by_number[8]["run_id"], by_number[8]["row"]) == ("a-jev-s1", 1)


def test_too_few_states_is_an_error_naming_both_numbers(tmp_path):
    make_run(tmp_path, "a-jev-s1", "jev", 1, [0, 1, 2])

    with pytest.raises(ValueError, match="only 3 distinct states .* 5 were asked"):
        load_dev_states(tmp_path, n=5)


def test_a_folder_without_a_result_is_skipped(tmp_path):
    make_run(tmp_path, "a-jev-s1", "jev", 1, [0, 1])
    (tmp_path / "half-written").mkdir()

    assert numbers_of(load_dev_states(tmp_path, n=2)) == [0, 1]


# --- the question in the opposite order ---------------------------------------------------------


def test_the_options_come_back_in_the_opposite_order():
    assert list(reversed_options(QUESTION)["criteria"]) == [S, R, K, E]


def test_nothing_but_the_order_changes():
    flipped = reversed_options(QUESTION)

    assert flipped["type"] == QUESTION["type"] and flipped["instructions"] == QUESTION["instructions"]
    assert flipped["criteria"] == QUESTION["criteria"]  # the same text for every option (dict equality ignores order)
    assert json.dumps(flipped) != json.dumps(QUESTION)  # and yet what is sent differs: the order is in the JSON


def test_the_original_question_is_left_alone():
    before = json.dumps(QUESTION)

    reversed_options(QUESTION)

    assert json.dumps(QUESTION) == before


def test_reversing_twice_gives_back_the_original():
    assert json.dumps(reversed_options(reversed_options(QUESTION))) == json.dumps(QUESTION)


def states(count):
    return [{"run_id": "r", "row": i, "state": a_state(i)} for i in range(count)]


def test_each_state_is_asked_three_times_current_reversed_and_current_again():
    requests = order_requests(states(2), QUESTION)

    assert VARIANTS == ("current", "reversed", "current_again")
    assert [(r["state_index"], r["variant"]) for r in requests] == [
        (0, "current"), (0, "reversed"), (0, "current_again"), (1, "current"), (1, "reversed"), (1, "current_again")]


def test_the_options_of_each_request_are_in_the_order_its_variant_says():
    orders = [list(r["questions"]["tactic"]["criteria"]) for r in order_requests(states(1), QUESTION)]

    assert orders == [OPTIONS, [S, R, K, E], OPTIONS]


def test_a_request_carries_its_state_and_where_the_state_came_from():
    request = order_requests(states(3), QUESTION)[4]  # the second state, in the opposite order

    assert request["state"] == a_state(1)
    assert (request["source_run"], request["source_row"]) == ("r", 1)
    assert request["order"] == [S, R, K, E]


# --- the numbers --------------------------------------------------------------------------------

VECTORS = {
    "current": {E: 0.5, K: 0.3, R: 0.1, S: 0.1},
    "reversed": {E: 0.4, K: 0.3, R: 0.1, S: 0.2},
    "current_again": {E: 0.5, K: 0.3, R: 0.1, S: 0.1},
}


def answer_row(index, variant, choice, error=None):
    answers = None if error else {"tactic": {"type": "choice", "choice": choice, "confidence": 0.5, "probabilities": VECTORS[variant]}}
    return {
        "state_index": index, "variant": variant, "answers": answers, "model": None if error else EXPECTED_MODEL,
        "input_tokens": 0 if error else 743, "cost": 0.0 if error else 0.00003, "cost_source": None if error else "usage.cost",
        "latency_ms": 300, "error": error,
    }


def triples(choices):
    """The rows of one state per entry: its (current, reversed, current_again) choices."""
    return [answer_row(i, variant, choice) for i, trio in enumerate(choices) for variant, choice in zip(VARIANTS, trio)]


#                 current reversed again
SCENARIO = [(E, E, E), (E, E, E), (E, K, E), (K, K, K), (K, K, K), (K, E, K), (R, R, R), (S, S, S), (E, S, E), (K, K, E)]
# between the orders the choice differs at states 2, 5 and 8 (3 of 10); asking the same order twice, at state 9 (1 of 10)


def test_how_often_the_choice_differs_between_the_orders_and_between_two_asks_of_the_same_order():
    order = summarize_order_check(triples(SCENARIO), requested=30, stopped=None, options=OPTIONS)["order"]

    assert order["states"] == 10 and order["incomplete_states"] == 0
    assert order["differs_between_orders"]["count"] == 3
    assert order["differs_between_orders"]["rate"] == pytest.approx(0.3)
    assert order["differs_between_orders"]["wilson95"] == pytest.approx(list(wilson_interval(3, 10)))
    assert order["differs_same_order"]["count"] == 1 and order["differs_same_order"]["rate"] == pytest.approx(0.1)


def test_how_often_the_first_and_the_last_listed_options_win_in_each_position():
    order = summarize_order_check(triples(SCENARIO), requested=30, stopped=None, options=OPTIONS)["order"]

    # ENGAGE is first in the current order and last in the opposite one; SEARCH is the other way round
    assert order["first_in_current"] == {"option": E, "chosen_listed_first": pytest.approx(0.4), "chosen_listed_last": pytest.approx(0.3)}
    assert order["last_in_current"] == {"option": S, "chosen_listed_first": pytest.approx(0.2), "chosen_listed_last": pytest.approx(0.1)}


def test_the_mean_probability_of_each_option_in_each_order():
    order = summarize_order_check(triples(SCENARIO), requested=30, stopped=None, options=OPTIONS)["order"]

    assert order["mean_probability"]["current"] == pytest.approx(VECTORS["current"])
    assert order["mean_probability"]["reversed"] == pytest.approx(VECTORS["reversed"])


def test_the_summary_keeps_the_numbers_every_probe_reports():
    summary = summarize_order_check(triples(SCENARIO), requested=30, stopped=None, options=OPTIONS)

    assert (summary["calls_requested"], summary["calls_made"], summary["ok"], summary["errors"]) == (30, 30, 30, 0)
    assert summary["spend_usd"] == pytest.approx(30 * 0.00003)
    assert summary["models"] == {EXPECTED_MODEL: 30}


@pytest.mark.parametrize("differing, not_neutral", [(0, False), (10, False), (11, True), (100, True)])
def test_the_order_is_not_neutral_only_when_more_than_10_percent_of_the_choices_differ(differing, not_neutral):
    choices = [(E, K if i < differing else E, E) for i in range(100)]

    order = summarize_order_check(triples(choices), requested=300, stopped=None, options=OPTIONS)["order"]

    assert order["limit"] == 0.1 and order["not_neutral"] is not_neutral


def test_a_state_with_a_failed_answer_is_left_out_of_the_comparison():
    rows = triples(SCENARIO)
    rows[1] = answer_row(0, "reversed", None, error="TypeSafeAPITimeoutError: timed out")

    summary = summarize_order_check(rows, requested=30, stopped=None, options=OPTIONS)

    assert (summary["order"]["states"], summary["order"]["incomplete_states"]) == (9, 1)
    assert (summary["ok"], summary["errors"]) == (29, 1)


def test_a_row_that_carries_an_error_is_never_used_even_if_it_also_has_an_answer():
    rows = triples(SCENARIO)
    rows[1] = {**answer_row(0, "reversed", K), "error": "TypeSafeAPITimeoutError: timed out"}

    order = summarize_order_check(rows, requested=30, stopped=None, options=OPTIONS)["order"]

    assert (order["states"], order["incomplete_states"]) == (9, 1)


def test_an_answer_that_is_not_one_of_the_options_does_not_count_either():
    rows = triples(SCENARIO)
    rows[2] = answer_row(0, "current_again", "FLEE")

    order = summarize_order_check(rows, requested=30, stopped=None, options=OPTIONS)["order"]

    assert (order["states"], order["incomplete_states"]) == (9, 1)


def test_a_probe_stopped_in_the_middle_of_a_state_counts_that_state_as_incomplete():
    order = summarize_order_check(triples(SCENARIO)[:7], requested=30, stopped="budget cap reached", options=OPTIONS)["order"]

    assert (order["states"], order["incomplete_states"]) == (2, 1)


def test_with_no_complete_state_there_is_nothing_to_compare():
    summary = summarize_order_check([], requested=30, stopped="budget cap reached", options=OPTIONS)

    assert summary["order"] is None and summary["calls_made"] == 0


def test_the_summary_line():
    result = {"run_id": "order-check-20261008T093000Z-darwin",
              **summarize_order_check(triples(SCENARIO), requested=30, stopped=None, options=OPTIONS)}

    assert describe_order_check(result) == (
        "order-check: 30 calls (30 ok, 0 errors) over 10 states | the choice differs between the two orders in 3 of 10 "
        "(30%, 95% interval 11-60%) | asking the same order twice it differs in 1 of 10 | ENGAGE is chosen 40% of the time "
        "listed first and 30% listed last; SEARCH 20% listed first and 10% listed last | the order is NOT neutral "
        "(more than 10% differ) | $0.000900 in all | [order-check-20261008T093000Z-darwin]")


def test_the_summary_line_says_when_the_order_looks_neutral():
    quiet = [(E, E, E)] * 10
    result = {"run_id": "x", **summarize_order_check(triples(quiet), requested=30, stopped=None, options=OPTIONS)}

    assert "the order looks neutral (10% or fewer differ)" in describe_order_check(result)


def test_the_summary_line_when_no_state_was_complete():
    result = {"run_id": "x", **summarize_order_check([], requested=30, stopped="budget cap reached", options=OPTIONS)}

    assert describe_order_check(result) == "order-check: 0 calls (0 ok, 0 errors) | no state was answered in all three ways | $0.000000 in all | [x]"


# --- the probe ----------------------------------------------------------------------------------


def check(runs_dir, api, count=3, cap_usd=1.0):
    async def scenario():
        async with client_for(api, cap_usd=cap_usd) as client:
            return await run_order_check(client, states(count), QUESTION, runs_dir=runs_dir, utc_now=lambda: FIXED)

    return run(scenario())


def rows_of(runs_dir):
    folder = next(runs_dir.iterdir())
    return [json.loads(line) for line in (folder / "decisions.jsonl").read_text().splitlines()]


def test_the_options_reach_the_wire_in_the_order_each_variant_says(tmp_path):
    # The whole check rests on this: if the client or the SDK sorted or rebuilt the options, the "opposite
    # order" would be the same request and the check would report that order never matters.
    api = FakeAPI((200, good()))

    check(tmp_path, api, count=2)

    orders = [list(request["body"]["questions"]["tactic"]["criteria"]) for request in api.requests]
    assert orders == [OPTIONS, [S, R, K, E], OPTIONS] * 2
    assert [request["body"]["state"] for request in api.requests] == [a_state(0)] * 3 + [a_state(1)] * 3


def test_every_call_has_its_row_and_the_folder_is_named_for_the_probe(tmp_path):
    result = check(tmp_path, FakeAPI((200, good())), count=2)

    folder = tmp_path / f"order-check-20261008T093000Z-{MACHINE}"
    assert result["run_id"] == folder.name and result["kind"] == "order-check"
    assert {p.name for p in folder.iterdir()} == {"decisions.jsonl", "result.json"}
    rows = rows_of(tmp_path)
    assert [r["call"] for r in rows] == [1, 2, 3, 4, 5, 6]
    assert [(r["state_index"], r["variant"]) for r in rows[:3]] == [(0, "current"), (0, "reversed"), (0, "current_again")]
    assert all(r["state"] == a_state(r["state_index"]) and r["error"] is None and r["model"] == EXPECTED_MODEL for r in rows)
    assert all({"source_run", "source_row", "order", "answers", "input_tokens", "cost", "latency_ms"} <= set(r) for r in rows)
    assert json.loads((folder / "result.json").read_text()) == result


def test_the_summary_is_computed_from_the_answers_received(tmp_path):
    # FakeAPI answers KITE every time with the same probabilities, whatever the order: nothing differs.
    result = check(tmp_path, FakeAPI((200, good())), count=3)

    assert result["order"]["states"] == 3
    assert result["order"]["options"] == OPTIONS  # in the order they were listed in the current question
    assert (result["order"]["first_in_current"]["option"], result["order"]["last_in_current"]["option"]) == (E, S)
    assert result["order"]["differs_between_orders"]["count"] == 0 and result["order"]["not_neutral"] is False


def test_the_ledger_counts_the_cost_once(tmp_path):
    result = check(tmp_path, FakeAPI((200, good(cost=0.00006))), count=3)

    ledger = read_ledger(tmp_path)

    assert ledger.spent == pytest.approx(9 * 0.00006) and (ledger.paid_calls, ledger.files) == (9, 1)
    assert result["spend_usd"] == pytest.approx(ledger.spent)


def test_reaching_the_cap_stops_it_and_says_how_far_it_got(tmp_path):
    result = check(tmp_path, FakeAPI((200, good(cost=0.00006))), count=10, cap_usd=0.0002)

    assert result["stopped"].startswith("budget cap reached")
    assert result["calls_made"] == 4 and result["calls_requested"] == 30
    assert (result["order"]["states"], result["order"]["incomplete_states"]) == (1, 1)


def test_a_different_answering_model_stops_it_after_that_call(tmp_path):
    api = FakeAPI((200, good(model="typesafe/jev-1.13-20260918")))

    result = check(tmp_path, api, count=3)

    assert len(api.requests) == 1 and result["stopped"].startswith("unexpected model")
