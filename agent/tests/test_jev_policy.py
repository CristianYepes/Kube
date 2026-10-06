import asyncio
import json
import logging
import time
from pathlib import Path

import pytest
from fake_jev import AutoClient, FakeClient, jev_result
from helpers import ROOM, enemy_ahead, floats_in, make_obs

from kube_agent import config
from kube_agent.jev_client import EXPECTED_MODEL
from kube_agent.policies import JevPolicy

THRESHOLD = 0.3
CLOSE = enemy_ahead(2.0, 0.0)  # a grunt under 2.5 cells away, in view
THREE = [enemy_ahead(2.0, 0.0), enemy_ahead(4.0, 1.0), enemy_ahead(5.0, -1.0)]
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "idle_seed7.jsonl"


def run(coroutine):
    return asyncio.run(asyncio.wait_for(coroutine, 20))


async def settle():
    """Let the request tasks run: a released request needs a turn of the event loop to finish."""
    for _ in range(3):
        await asyncio.sleep(0)


def new_policy(client, **kwargs):
    return JevPolicy(ROOM, client, threshold=THRESHOLD, **kwargs)


async def first_answer(client, policy, **answer):
    """Step once to send request 1, release it with `answer`, and step again to receive it."""
    policy.step(make_obs([CLOSE], t=0.0))
    await settle()
    client.release(**answer)
    await settle()
    return policy.step(make_obs([CLOSE], t=0.1))


# --- sending ------------------------------------------------------------------------------------


def test_it_starts_on_engage_and_the_first_observation_sends_one_request_and_no_row():
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        row = policy.step(make_obs([CLOSE], t=0.0))
        await settle()
        return client, policy, row

    client, policy, row = run(scenario())

    assert row is None and policy.tactic == "ENGAGE"
    assert len(client.calls) == 1
    sent = client.calls[0]
    assert sent["state"]["current_tactic"] == "ENGAGE" and sent["state"]["threats"]["close_count"] == 1
    assert sent["questions"] == config.questions()


def test_the_threshold_defaults_to_the_one_in_the_config():
    assert JevPolicy(ROOM, FakeClient())._threshold == config.CONFIDENCE_THRESHOLD == 0.3


# --- the confidence gate (AC7) ------------------------------------------------------------------


@pytest.mark.parametrize("confidence, applied", [(0.29, False), (0.3, True), (0.31, True), (0.95, True)])
def test_ac7_an_answer_is_applied_only_from_the_threshold_up(confidence, applied):
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        row = await first_answer(client, policy, choice="KITE", confidence=confidence)
        return policy, row

    policy, row = run(scenario())

    assert row["applied"] is applied
    assert policy.tactic == ("KITE" if applied else "ENGAGE")
    assert row["tactic"] == "KITE"  # what Jev chose is logged whether or not it was applied
    assert row["reason"] == (None if applied else "below_threshold")


def test_a_decision_row_has_the_fields_of_ac9_and_the_times_of_the_request():
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        return await first_answer(client, policy, choice="KITE", confidence=0.8, cost=0.00003, tokens=743, latency_ms=300)

    row = run(scenario())

    assert (row["source"], row["t"], row["answered_at"], row["stale"]) == ("jev", 0.0, 0.1, False)
    assert (row["model"], row["input_tokens"], row["cost"], row["latency_ms"], row["confidence"]) == (
        EXPECTED_MODEL, 743, 0.00003, 300, 0.8)
    assert row["answers"]["tactic"]["choice"] == "KITE" and row["error"] is None
    assert row["state"]["current_tactic"] == "ENGAGE"  # the state shows the tactic it replaces


def test_a_failed_call_leaves_the_tactic_and_the_next_decision_goes_out_on_schedule():
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        row = await first_answer(client, policy, error="TypeSafeAPITimeoutError: no answer in 4.0 s")
        calls_after_the_failure = len(client.calls)
        policy.step(make_obs([CLOSE], t=0.3))  # not due yet
        policy.step(make_obs([CLOSE], t=0.5))  # due: the next request
        await settle()
        return policy, client, row, calls_after_the_failure

    policy, client, row, calls_after_the_failure = run(scenario())

    assert (row["applied"], row["reason"], row["tactic"], row["confidence"]) == (False, "error", None, None)
    assert row["error"].startswith("TypeSafeAPITimeoutError")
    assert policy.tactic == "ENGAGE"
    assert (calls_after_the_failure, len(client.calls)) == (1, 2)


def test_a_choice_that_is_not_a_tactic_is_not_applied():
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        row = await first_answer(client, policy, choice="FLEE", confidence=0.9)
        return policy, row

    policy, row = run(scenario())

    assert (row["applied"], row["reason"], row["tactic"]) == (False, "malformed", None)
    assert policy.tactic == "ENGAGE"


# --- one request at a time, and never blocking --------------------------------------------------


def test_only_one_request_is_in_flight_and_the_next_goes_out_when_it_returns_with_a_fresh_state():
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        policy.step(make_obs(THREE, t=0.0))
        for t in (0.1, 0.5, 0.9, 1.0, 1.4):  # the half second passes twice and nothing is released
            policy.step(make_obs(THREE, t=t))
        await settle()
        in_flight = len(client.calls)
        client.release(confidence=0.9)
        await settle()
        row = policy.step(make_obs([CLOSE], t=1.5))  # two enemies are gone: the new state must show it
        await settle()
        return in_flight, client, row

    in_flight, client, row = run(scenario())

    assert in_flight == 1
    assert row["applied"] is True  # the half seconds that passed were not events: the answer stands
    assert len(client.calls) == 2
    assert client.calls[1]["state"]["threats"]["remaining"] == 1


def test_a_slow_request_never_blocks_the_loop():
    class Slow(FakeClient):
        async def ask(self, state, questions):
            self.calls.append({"state": state, "questions": questions})
            await asyncio.sleep(0.15)
            return jev_result(confidence=0.9)

    async def scenario():
        policy = new_policy(Slow())
        steps, slowest, row = 0, 0.0, None
        started = time.monotonic()
        while row is None and time.monotonic() - started < 5:
            begin = time.monotonic()
            row = policy.step(make_obs([CLOSE], t=steps * 0.01))
            slowest = max(slowest, time.monotonic() - begin)
            steps += 1
            await asyncio.sleep(0.005)
        return steps, slowest

    steps, slowest = run(scenario())

    assert steps >= 15  # the game loop went on for the 0.15 s that the request took
    assert slowest < 0.02  # and no single step waited for it


# --- stale answers ------------------------------------------------------------------------------


@pytest.mark.parametrize("event", [{"wave": 2}, {"hp": 20}])
def test_an_answer_whose_state_predates_an_event_is_not_applied_and_a_new_request_follows(event):
    # AC of T7: a new wave, or health dropping a band, after the state was sent makes the answer stale.
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        policy.step(make_obs(THREE, t=0.0))
        policy.step(make_obs(THREE, t=0.1, **event))  # the event, while request 1 is out
        await settle()
        client.release(0, choice="KITE", confidence=0.9)
        await settle()
        row = policy.step(make_obs(THREE, t=0.2, **event))
        await settle()
        return client, policy, row

    client, policy, row = run(scenario())

    assert (row["applied"], row["reason"], row["stale"]) == (False, "stale", True)
    assert row["tactic"] == "KITE" and policy.tactic == "ENGAGE"
    assert len(client.calls) == 2  # a new request went out at once, in the same step
    fresh = client.calls[1]["state"]
    assert fresh["progress"]["wave"] == ("2 of 3" if "wave" in event else "1 of 3")
    assert fresh["player"]["health"] == ("low" if "hp" in event else "high")


def test_an_event_on_the_very_frame_the_answer_arrives_still_makes_it_stale():
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        policy.step(make_obs(THREE, t=0.0))
        await settle()
        client.release(0, choice="KITE", confidence=0.9)
        await settle()
        return policy.step(make_obs(THREE, t=0.1, wave=2))  # the answer and the new wave on the same observation

    row = run(scenario())

    assert (row["applied"], row["reason"]) == (False, "stale")


def test_a_request_sent_on_the_event_itself_is_not_stale():
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        await first_answer(client, policy, choice="ENGAGE", confidence=0.9)
        policy.step(make_obs(THREE, t=0.2, wave=2))  # the event: no request is out, so one goes out now
        await settle()
        client.release(choice="KITE", confidence=0.9)
        await settle()
        return policy.step(make_obs(THREE, t=0.3, wave=2))

    row = run(scenario())

    assert (row["applied"], row["stale"]) == (True, False)


# --- the budget ---------------------------------------------------------------------------------


def test_the_call_that_reaches_the_cap_is_applied_and_the_rules_decide_from_then_on(caplog):
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        policy.step(make_obs([CLOSE], t=0.0))
        await settle()
        client.release(choice="RETREAT", confidence=0.9, exhaust=True)
        await settle()
        jevs_last = policy.step(make_obs([CLOSE], t=0.1))
        rules_close = policy.step(make_obs([CLOSE], t=0.5))  # the next decision is due
        rules_hidden = policy.step(make_obs([enemy_ahead(5.0, 0.0, los=0)], t=1.0))
        await settle()
        return client, jevs_last, rules_close, rules_hidden

    with caplog.at_level(logging.WARNING, logger="kube_agent.jev"):
        client, jevs_last, rules_close, rules_hidden = run(scenario())

    assert (jevs_last["source"], jevs_last["applied"], jevs_last["tactic"]) == ("jev", True, "RETREAT")
    assert (rules_close["source"], rules_close["tactic"], rules_close["applied"]) == ("scripted_fallback", "KITE", True)
    assert rules_hidden["tactic"] == "SEARCH"
    assert len(client.calls) == 1  # no request after the cap
    assert len([r for r in caplog.records if "budget cap reached" in r.getMessage()]) == 1  # said once, out loud


def test_an_answer_that_arrives_after_the_switch_to_the_rules_is_not_applied():
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        policy.step(make_obs([CLOSE], t=0.0))
        await settle()
        client.exhausted = True  # the cap is reached while request 1 is still out
        during = policy.step(make_obs([CLOSE], t=0.1))
        client.release(choice="RETREAT", confidence=0.9)
        await settle()
        late = policy.step(make_obs([CLOSE], t=0.2))
        tactic_after_the_late_answer = policy.tactic
        rules = policy.step(make_obs([CLOSE], t=0.5))
        return during, late, tactic_after_the_late_answer, rules

    during, late, tactic_after_the_late_answer, rules = run(scenario())

    assert during is None
    assert (late["applied"], late["reason"]) == (False, "fallback")
    assert tactic_after_the_late_answer == "ENGAGE"  # RETREAT was not applied
    assert (rules["source"], rules["tactic"]) == ("scripted_fallback", "KITE")


def test_a_finished_answer_is_never_lost_to_the_rules_decision_that_follows_it():
    # The same step finishes request 1 (which reaches the cap) and finds a decision owed. One step
    # returns one row, so the answer's row comes first and the rules decide on the next step.
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        policy.step(make_obs([CLOSE], t=0.0))
        policy.step(make_obs([CLOSE], t=0.5))  # a decision is due while request 1 is out: it is owed
        await settle()
        client.release(choice="RETREAT", confidence=0.9, exhaust=True)
        await settle()
        first = policy.step(make_obs([CLOSE], t=0.6))
        second = policy.step(make_obs([CLOSE], t=0.61))
        return first, second, len(client.calls)

    first, second, calls = run(scenario())

    assert (first["source"], first["tactic"], first["applied"]) == ("jev", "RETREAT", True)
    assert (second["source"], second["tactic"]) == ("scripted_fallback", "KITE")
    assert calls == 1  # no new request: the budget is spent


def test_with_the_budget_already_spent_the_rules_decide_from_the_first_observation(caplog):
    client = FakeClient()
    client.exhausted = True
    policy = new_policy(client)

    async def scenario():
        return policy.step(make_obs([CLOSE], t=0.0))

    with caplog.at_level(logging.WARNING, logger="kube_agent.jev"):
        row = run(scenario())

    assert (row["source"], row["tactic"]) == ("scripted_fallback", "KITE")
    assert client.calls == []
    assert any("budget cap reached" in r.getMessage() for r in caplog.records)


# --- closing ------------------------------------------------------------------------------------


def test_closing_with_nothing_in_flight_returns_no_rows():
    async def scenario():
        policy = new_policy(FakeClient())
        return await policy.aclose()

    assert run(scenario()) == []


def test_closing_waits_for_the_request_in_flight_and_keeps_its_cost():
    # A paid call whose answer arrives after the episode ended must still reach the ledger.
    async def scenario():
        client = FakeClient()
        policy = new_policy(client)
        policy.step(make_obs([CLOSE], t=0.0))
        await settle()

        async def answer_later():
            await asyncio.sleep(0.05)
            client.release(choice="KITE", confidence=0.9, cost=0.00003)

        asyncio.create_task(answer_later())
        return await policy.aclose()

    rows = run(scenario())

    assert len(rows) == 1
    assert (rows[0]["applied"], rows[0]["reason"], rows[0]["cost"]) == (False, "episode_ended", 0.00003)
    assert rows[0]["tactic"] == "KITE" and rows[0]["source"] == "jev"


def test_closing_gives_up_on_a_request_that_never_answers_and_says_so(caplog):
    async def scenario():
        client = FakeClient()
        policy = new_policy(client, close_wait=0.05)
        policy.step(make_obs([CLOSE], t=0.0))
        await settle()
        return await policy.aclose()

    with caplog.at_level(logging.WARNING, logger="kube_agent.jev"):
        rows = run(scenario())

    assert rows == []
    assert any("still in flight" in r.getMessage() for r in caplog.records)


# --- over a whole recorded game (AC6) -----------------------------------------------------------


def test_ac6_every_state_of_a_whole_recorded_game_is_small_and_holds_no_float():
    recorded = [json.loads(line) for line in FIXTURE.read_text().splitlines()]

    async def scenario():
        client = AutoClient(choice="KITE", confidence=0.9)
        policy = JevPolicy(recorded[0]["map"], client, threshold=THRESHOLD)
        rows = []
        for obs in recorded[1:]:
            row = policy.step(obs)
            if row:
                rows.append(row)
            await asyncio.sleep(0)  # the answer comes back on the next turn of the loop
        return rows, client

    rows, client = run(scenario())

    assert 8 <= len(rows) <= 14  # about every 0.5 s over 4.9 s of game, plus events
    assert len(client.calls) in (len(rows), len(rows) + 1)  # a request may still be out at the end
    for row in rows:
        text = json.dumps(row["state"])
        assert len(text) < 2000 and not list(floats_in(row["state"]))
    assert all(row["applied"] for row in rows) and rows[-1]["tactic"] == "KITE"
