import asyncio
import json
import logging
import time

import httpx2
import pytest
from fake_jev import (
    FAST_RETRY,
    GUARD_SECONDS,
    KEY,
    PROBABILITIES,
    QUESTIONS,
    STATE,
    FakeAPI,
    SlowAPI,
    client_for,
    good,
)
from typesafe_sdk import RetryPolicy

from kube_agent import jev_client
from kube_agent.jev_client import (
    EXPECTED_MODEL,
    KEY_VARIABLE,
    BudgetExhausted,
    JevClient,
    KeyMissing,
)


def run(coroutine):
    return asyncio.run(asyncio.wait_for(coroutine, GUARD_SECONDS))


async def ask_once(client):
    async with client:
        return await client.ask(STATE, QUESTIONS)


# --- what is sent -------------------------------------------------------------------------------


def test_the_request_goes_to_openrouter_with_the_pinned_model_and_the_key():
    api = FakeAPI((200, good()))

    run(ask_once(client_for(api)))

    sent = api.requests[0]
    assert sent["url"] == "https://openrouter.ai/api/v1/systemone"
    assert sent["auth"] == f"Bearer {KEY}"
    assert sent["body"]["model"] == "typesafe/jev-1.13"  # the pinned alias, never jev-latest
    assert sent["body"]["state"] == STATE
    question = sent["body"]["questions"]["tactic"]
    assert question["type"] == "choice"
    assert list(question["criteria"]) == ["ENGAGE", "KITE", "RETREAT", "SEARCH"]  # the order is kept


# --- what comes back ----------------------------------------------------------------------------


def test_a_good_answer_carries_the_choice_and_the_accounting():
    result = run(ask_once(client_for(FakeAPI((200, good())))))

    assert result.error is None
    assert result.answers["tactic"]["choice"] == "KITE"
    assert result.answers["tactic"]["confidence"] == 0.82
    assert result.answers["tactic"]["probabilities"] == PROBABILITIES
    assert (result.model, result.input_tokens, result.cost) == (EXPECTED_MODEL, 1300, 0.000054)
    assert isinstance(result.latency_ms, int) and result.latency_ms >= 0


def test_the_row_has_the_fields_ac9_asks_for_and_is_plain_json():
    result = run(ask_once(client_for(FakeAPI((200, good())))))

    row = result.to_row()

    assert set(row) == {"answers", "model", "input_tokens", "cost", "cost_source", "latency_ms", "request_id", "error"}
    assert json.loads(json.dumps(row)) == row


def test_latency_is_measured_around_the_whole_call():
    result = run(ask_once(client_for(SlowAPI(delay=0.08))))

    assert 70 <= result.latency_ms < 1500  # asked to wait 80 ms; a little slack for the clock


def test_the_cost_comes_from_the_raw_json_and_falls_back_to_the_price_per_token():
    # OpenRouter sends usage.cost. Without it, input tokens times $0.042 per million.
    with_cost = run(ask_once(client_for(FakeAPI((200, good(cost=0.000123))))))
    without = run(ask_once(client_for(FakeAPI((200, good(cost=None, tokens=2000))))))

    assert with_cost.cost == 0.000123
    assert without.cost == pytest.approx(2000 * 0.042 / 1_000_000)
    # and the row says which of the two it is, so the ledger can be audited
    assert (with_cost.cost_source, without.cost_source) == ("usage.cost", "price_per_token")


@pytest.mark.parametrize("bad_cost", ["0.1", -1, True])
def test_a_cost_that_makes_no_sense_is_replaced_by_the_price_per_token(bad_cost):
    result = run(ask_once(client_for(FakeAPI((200, good(cost=bad_cost, tokens=1000))))))

    assert result.error is None
    assert result.cost == pytest.approx(1000 * 0.042 / 1_000_000)
    assert result.cost_source == "price_per_token"


def test_a_missing_request_id_header_does_not_raise_and_a_present_one_is_kept():
    # SystemOneResponse.request_id raises when the header is missing, and OpenRouter does not send it.
    missing = run(ask_once(client_for(FakeAPI((200, good())))))
    present = run(ask_once(client_for(FakeAPI((200, good(), {"x-typesafe-request-id": "req-123"})))))

    assert missing.error is None and missing.request_id is None
    assert present.request_id == "req-123"


@pytest.mark.parametrize("literal", ["NaN", "Infinity", "-Infinity"])
def test_a_cost_that_is_not_a_finite_number_is_replaced_by_the_price_per_token(literal):
    # httpx2 will not serialise these with json=, so they are sent as raw bytes, as a server could.
    raw = (
        '{"model":"%s","answers":{"tactic":{"type":"choice","choice":"A","confidence":0.8,"probabilities":{"A":1.0}}},'
        '"usage":{"input_tokens":1000,"output_tokens":5,"cost":%s}}' % (EXPECTED_MODEL, literal)
    ).encode()

    def api(request):
        return httpx2.Response(200, content=raw, headers={"content-type": "application/json"})

    result = run(ask_once(client_for(api)))

    assert result.error is None
    assert result.cost == pytest.approx(1000 * 0.042 / 1_000_000)
    assert result.cost_source == "price_per_token"


# --- the model that answered --------------------------------------------------------------------


def test_a_different_answering_model_warns_once_per_model_and_still_answers(caplog):
    newer = "typesafe/jev-1.13-20260918"
    api = FakeAPI((200, good(model=EXPECTED_MODEL)), (200, good(model=newer)), (200, good(model=newer)), (200, good(model="typesafe/jev-9")))

    async def scenario():
        async with client_for(api) as client:
            return [await client.ask(STATE, QUESTIONS) for _ in range(4)]

    with caplog.at_level(logging.WARNING, logger="kube_agent.jev"):
        results = run(scenario())

    assert [r.model for r in results] == [EXPECTED_MODEL, newer, newer, "typesafe/jev-9"]
    assert all(r.error is None for r in results)  # a different model is a warning, not a failure
    warnings = [r.getMessage() for r in caplog.records if "answering model" in r.getMessage()]
    assert len(warnings) == 2  # the first sight of each new model, not one per call
    assert newer in warnings[0] and EXPECTED_MODEL in warnings[0]
    assert "typesafe/jev-9" in warnings[1]


# --- retries (AC8, FR8) -------------------------------------------------------------------------


def test_429_then_529_then_success_is_retried_and_the_loop_keeps_ticking():
    api = FakeAPI((429, {"detail": "slow down"}), (529, {"detail": "overloaded"}), (200, good()))
    slow_retry = RetryPolicy(max_retries=2, backoff_initial=0.05, backoff_max=0.1, backoff_jitter=0.0, timeout=3.0)

    async def scenario():
        ticks = 0

        async def ticker():
            nonlocal ticks
            while True:
                await asyncio.sleep(0.005)
                ticks += 1

        task = asyncio.create_task(ticker())
        result = await ask_once(client_for(api, retry=slow_retry))
        task.cancel()
        return result, ticks

    result, ticks = run(scenario())

    assert len(api.requests) == 3
    assert result.error is None and result.answers["tactic"]["choice"] == "KITE"
    assert ticks >= 10  # the two waits (0.15 s in all) did not block the event loop


def test_when_every_attempt_fails_nothing_is_raised_and_the_row_says_why():
    api = FakeAPI((500, {"detail": "boom"}))

    result = run(ask_once(client_for(api)))

    assert len(api.requests) == 3  # the first attempt and two retries
    assert result.answers is None and result.model is None
    assert (result.input_tokens, result.cost, result.cost_source) == (0, 0.0, None)
    assert result.error.startswith("TypeSafeInternalServerError") and "500" in result.error


def test_a_connection_error_is_retried_and_then_reported():
    def refuse(request):
        raise httpx2.ConnectError("no route", request=request)

    api = FakeAPI(refuse)

    result = run(ask_once(client_for(api)))

    assert len(api.requests) == 3
    assert result.error.startswith("TypeSafeAPIConnectionError")


def test_a_status_that_is_not_retryable_is_tried_once():
    api = FakeAPI((422, {"detail": "bad question"}))

    result = run(ask_once(client_for(api)))

    assert len(api.requests) == 1
    assert result.error.startswith("TypeSafeUnprocessableEntityError")


def test_a_malformed_answer_is_an_error_row_and_not_an_exception():
    result = run(ask_once(client_for(FakeAPI((200, {"nonsense": True})))))

    assert result.error.startswith("TypeSafeAPIResponseValidationError")
    assert result.answers is None


def test_a_retry_after_longer_than_the_retry_budget_is_not_waited_for():
    # RetryPolicy.timeout is the budget for the whole call, checked between attempts: a Retry-After of
    # 30 s against a 3 s budget stops the retrying at once instead of sleeping.
    api = FakeAPI((429, {"detail": "slow down"}, {"retry-after": "30"}))
    started = time.monotonic()

    result = run(ask_once(JevClient(KEY, cap_usd=1.0, transport=httpx2.MockTransport(api))))  # the real policy

    assert time.monotonic() - started < 1.5
    assert len(api.requests) == 1
    assert result.error.startswith("TypeSafeRateLimitError")


def test_an_attempt_that_never_answers_is_cut_by_the_hard_limit_and_the_client_stays_usable(monkeypatch):
    # The SDK's own timeout lives in the transport and does not apply to a handler that just waits,
    # so the only bound on an attempt in flight is asyncio.timeout around the whole call.
    monkeypatch.setattr(jev_client, "HARD_LIMIT", 0.3)
    api = SlowAPI(delay=10)

    async def scenario():
        async with client_for(api) as client:
            first = await client.ask(STATE, QUESTIONS)
            api.delay = 0.0
            second = await client.ask(STATE, QUESTIONS)
            return first, second

    first, second = run(scenario())

    assert first.error.startswith("TimeoutError") and "0.3" in first.error
    assert 290 <= first.latency_ms < 1500  # cut at 0.3 s; a little slack for the clock
    assert second.error is None  # nothing was left broken


def test_cancelling_a_call_cancels_it_and_is_not_turned_into_an_error_row():
    # The policy cancels a request that went stale: that must reach the caller as a cancellation.
    api = SlowAPI(delay=10)

    async def scenario():
        async with client_for(api) as client:
            task = asyncio.create_task(client.ask(STATE, QUESTIONS))
            await asyncio.sleep(0.05)
            task.cancel()
            await task

    with pytest.raises(asyncio.CancelledError):
        run(scenario())


def test_the_error_text_is_cut_to_a_short_length():
    api = FakeAPI((500, {"detail": "x" * 5000}))

    result = run(ask_once(client_for(api)))

    assert result.error.startswith("TypeSafeInternalServerError")
    assert len(result.error) <= 300


def test_the_timeout_reaches_the_transport_for_each_phase_of_an_attempt():
    # httpx applies one number to connect, read, write and pool separately: it is not a cap on the attempt.
    seen = {}

    def api(request):
        seen.update(request.extensions["timeout"])
        return httpx2.Response(200, json=good())

    run(ask_once(client_for(api)))

    assert seen == {"connect": 1.5, "read": 1.5, "write": 1.5, "pool": 1.5}


def test_the_real_retry_policy_retries_twice_inside_a_budget_shorter_than_the_hard_limit():
    policy = jev_client.DEFAULT_RETRY

    assert policy.max_retries == 2
    assert policy.timeout < jev_client.HARD_LIMIT  # the retries give up before the hard stop would cut them
    assert 429 in policy.http_statuses and 529 in policy.http_statuses and policy.respect_retry_after


# --- the budget cap (AC10, FR10) ----------------------------------------------------------------


def test_with_a_cap_of_a_hundredth_of_a_cent_the_calls_stop_after_it_and_say_why(caplog):
    api = FakeAPI((200, good(cost=0.00006)))

    async def scenario():
        async with client_for(api, cap_usd=0.0001) as client:
            results = [await client.ask(STATE, QUESTIONS) for _ in range(4)]
            return results, client

    with caplog.at_level(logging.WARNING, logger="kube_agent.jev"):
        results, client = run(scenario())

    assert len(api.requests) == 2  # 0.00006 spent, then 0.00012: the cap is reached, so no third call
    assert [r.error is None for r in results] == [True, True, False, False]
    skipped = results[2]
    assert "budget cap reached" in skipped.error and "$0.000120" in skipped.error and "$0.000100" in skipped.error
    assert (skipped.answers, skipped.model, skipped.cost, skipped.latency_ms) == (None, None, 0.0, 0)
    assert client.exhausted and client.spent == pytest.approx(0.00012)
    assert len([r for r in caplog.records if "budget cap reached" in r.getMessage()]) == 1  # said once, out loud


def test_a_cap_of_zero_makes_no_call_at_all():
    api = FakeAPI((200, good()))

    result = run(ask_once(client_for(api, cap_usd=0.0)))

    assert api.requests == []
    assert "budget cap reached" in result.error


def test_a_failed_call_costs_nothing_against_the_cap():
    api = FakeAPI((500, {"detail": "boom"}))

    async def scenario():
        async with client_for(api, cap_usd=0.0001) as client:
            await client.ask(STATE, QUESTIONS)
            return client.spent

    assert run(scenario()) == 0.0


# --- starting from the environment and the ledger -----------------------------------------------


def write_ledger(folder, costs):
    folder.mkdir(parents=True)
    (folder / "decisions.jsonl").write_text("".join(json.dumps({"cost": c}) + "\n" for c in costs))


def test_a_missing_key_is_reported_by_the_name_of_its_variable(tmp_path):
    with pytest.raises(KeyMissing) as error:
        JevClient.from_environment(cap_usd=0.05, runs_dir=tmp_path, environ={})

    assert KEY_VARIABLE == "OPENROUTER_API_KEY" and KEY_VARIABLE in str(error.value)


def test_an_empty_key_counts_as_missing(tmp_path):
    with pytest.raises(KeyMissing):
        JevClient.from_environment(cap_usd=0.05, runs_dir=tmp_path, environ={KEY_VARIABLE: "   "})


def test_the_cap_is_the_smaller_of_the_one_asked_for_and_what_the_ledger_has_left(tmp_path):
    write_ledger(tmp_path / "earlier-run", [0.5, 0.47])  # $0.97 spent, $0.03 left

    asks_for_more = JevClient.from_environment(cap_usd=0.50, runs_dir=tmp_path, environ={KEY_VARIABLE: KEY})
    asks_for_less = JevClient.from_environment(cap_usd=0.01, runs_dir=tmp_path, environ={KEY_VARIABLE: KEY})

    assert asks_for_more.cap_usd == pytest.approx(0.03)
    assert asks_for_less.cap_usd == 0.01


def test_a_ledger_that_adds_up_to_one_dollar_refuses_to_start(tmp_path):
    write_ledger(tmp_path / "earlier-run", [0.1] * 10)

    with pytest.raises(BudgetExhausted, match=r"\$1\.00 total budget is spent"):
        JevClient.from_environment(cap_usd=0.05, runs_dir=tmp_path, environ={KEY_VARIABLE: KEY})


# --- the key never leaves its variable (FR13) ---------------------------------------------------


def test_a_server_that_echoes_the_key_in_an_error_does_not_get_it_into_the_row():
    # Seen in the SDK: the text of an API error includes the body the server sent.
    api = FakeAPI((401, {"detail": f"invalid key {KEY}"}))

    result = run(ask_once(client_for(api)))

    assert result.error.startswith("TypeSafeAuthenticationError")
    assert KEY not in result.error and "[key]" in result.error
    assert KEY not in json.dumps(result.to_row())


def test_the_key_does_not_show_in_the_clients_text():
    client = client_for(FakeAPI((200, good())))

    assert KEY not in repr(client) and KEY not in str(client)
