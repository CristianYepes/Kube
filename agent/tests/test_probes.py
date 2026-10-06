import asyncio
import json
import platform
from datetime import datetime, timezone

import httpx2
import pytest
from fake_jev import FAST_RETRY, GUARD_SECONDS, FakeAPI, client_for, good
from helpers import floats_in

from kube_agent import config
from kube_agent.jev_client import EXPECTED_MODEL
from kube_agent.ledger import read_ledger
from kube_agent.probes import fixture_state, percentile, run_latency, summarize_latency

QUESTIONS = config.questions()
FIXED = datetime(2026, 10, 6, 9, 30, 0, tzinfo=timezone.utc)
MACHINE = platform.system().lower()
STATE = {"player": {"health": "high"}, "threats": {"remaining": 3}}
ROW_FIELDS = {"call", "state", "answers", "model", "input_tokens", "cost", "cost_source", "latency_ms", "request_id", "error"}


def run(coroutine):
    return asyncio.run(asyncio.wait_for(coroutine, GUARD_SECONDS))


def probe(runs_dir, api, n=5, cap_usd=1.0, retry=FAST_RETRY, utc_now=lambda: FIXED):
    async def scenario():
        async with client_for(api, cap_usd=cap_usd, retry=retry) as client:
            return await run_latency(client, STATE, QUESTIONS, n, runs_dir=runs_dir, utc_now=utc_now)

    return run(scenario())


def rows_of(runs_dir):
    folder = next(runs_dir.iterdir())
    return [json.loads(line) for line in (folder / "decisions.jsonl").read_text().splitlines()]


# --- the state that is sent ---------------------------------------------------------------------


def test_the_probe_state_is_a_small_real_state_with_a_threat_close_by():
    state = fixture_state()

    assert state["threats"]["close_count"] >= 1
    assert state["threats"]["nearest"]["distance"] in ("close", "touching")
    assert state["current_tactic"] == "ENGAGE"
    assert len(json.dumps(state)) < 2000 and not list(floats_in(state))  # AC6


def test_a_frame_past_the_end_of_the_recording_is_a_clear_error():
    with pytest.raises(ValueError, match="frame 99999 .* 464 observations"):
        fixture_state(frame=99999)


# --- percentiles and the summary ----------------------------------------------------------------


@pytest.mark.parametrize("values, q, expected", [
    ([7], 0.5, 7), ([7], 0.95, 7),
    ([1, 2, 3, 4, 5], 0.5, 3),  # ceil(2.5) = the 3rd
    ([1, 2, 3, 4, 5], 0.95, 5),  # ceil(4.75) = the 5th
    (list(range(1, 51)), 0.5, 25),  # n = 50: the 25th
    (list(range(1, 51)), 0.95, 48),  # n = 50: the 48th
    ([1, 2, 3, 4, 5], 0.0, 1),
    ([1, 2, 3, 4, 5], 1.0, 5),
])
def test_percentile_is_the_nearest_rank(values, q, expected):
    assert percentile(values, q) == expected


def row(latency=10, tokens=1300, cost=0.00005, source="usage.cost", model=EXPECTED_MODEL, error=None):
    return {"latency_ms": latency, "input_tokens": tokens, "cost": cost, "cost_source": source, "model": model, "error": error}


def test_the_summary_is_computed_over_the_answered_calls_only():
    rows = [row(latency=ms) for ms in range(1, 51)] + [row(latency=9999, tokens=0, cost=0.0, source=None, model=None, error="boom")] * 3

    summary = summarize_latency(rows, requested=60, stopped=None)

    assert (summary["calls_requested"], summary["calls_made"], summary["ok"], summary["errors"]) == (60, 53, 50, 3)
    assert summary["latency_ms"] == {"p50": 25, "p95": 48, "min": 1, "max": 50, "mean": 25.5}  # the 9999s are errors
    assert summary["input_tokens_per_call"] == 1300
    assert summary["cost_per_call_usd"] == pytest.approx(0.00005)
    assert summary["spend_usd"] == pytest.approx(50 * 0.00005)
    assert summary["models"] == {EXPECTED_MODEL: 50} and summary["cost_sources"] == {"usage.cost": 50}
    assert summary["stopped"] is None


def test_a_summary_with_no_answer_has_no_latency():
    summary = summarize_latency([row(error="boom", model=None, source=None, tokens=0, cost=0.0)], requested=5, stopped="3 errors in a row")

    assert summary["latency_ms"] is None and summary["cost_per_call_usd"] is None
    assert (summary["ok"], summary["errors"], summary["stopped"]) == (0, 1, "3 errors in a row")


# --- the probe ----------------------------------------------------------------------------------


def test_it_makes_the_calls_one_after_the_other_and_writes_a_row_for_each(tmp_path):
    api = FakeAPI((200, good()))

    result = probe(tmp_path, api, n=5)

    assert len(api.requests) == 5
    rows = rows_of(tmp_path)
    assert [r["call"] for r in rows] == [1, 2, 3, 4, 5]
    assert all(set(r) == ROW_FIELDS for r in rows)
    assert all(r["state"] == STATE and r["error"] is None and r["model"] == EXPECTED_MODEL for r in rows)
    assert all(isinstance(r["latency_ms"], int) and r["input_tokens"] == 1300 for r in rows)
    assert result["ok"] == 5 and result["stopped"] is None


def test_only_one_request_is_ever_in_flight(tmp_path):
    class Counting:
        def __init__(self):
            self.now = self.peak = self.total = 0

        async def __call__(self, request):
            self.now += 1
            self.peak = max(self.peak, self.now)
            self.total += 1
            await asyncio.sleep(0.01)
            self.now -= 1
            return httpx2.Response(200, json=good())

    api = Counting()

    probe(tmp_path, api, n=6)

    assert (api.peak, api.total) == (1, 6)


def test_the_folder_is_named_for_the_probe_the_time_and_the_machine_and_holds_two_files(tmp_path):
    result = probe(tmp_path, FakeAPI((200, good())), n=2)

    folder = tmp_path / f"latency-20261006T093000Z-{MACHINE}"
    assert result["run_id"] == folder.name
    assert {p.name for p in folder.iterdir()} == {"decisions.jsonl", "result.json"}
    assert json.loads((folder / "result.json").read_text()) == result
    assert (result["kind"], result["machine"], result["config_sha256"]) == ("latency", MACHINE, config.config_sha256())


def test_the_ledger_counts_the_probes_cost_once(tmp_path):
    result = probe(tmp_path, FakeAPI((200, good(cost=0.00006))), n=4)

    ledger = read_ledger(tmp_path)

    assert ledger.spent == pytest.approx(4 * 0.00006)
    assert (ledger.paid_calls, ledger.files) == (4, 1)  # result.json repeats the cost and is not read
    assert result["spend_usd"] == pytest.approx(ledger.spent)


def test_a_different_answering_model_stops_the_probe_after_that_call(tmp_path):
    # 🛑 of T6b: if the model that answers is not the expected one, stop and tell the owner.
    api = FakeAPI((200, good(model="typesafe/jev-1.13-20260918")))

    result = probe(tmp_path, api, n=50)

    assert len(api.requests) == 1
    assert result["stopped"].startswith("unexpected model") and "typesafe/jev-1.13-20260918" in result["stopped"]
    assert len(rows_of(tmp_path)) == 1  # the call that was paid for is in the ledger


def test_three_errors_in_a_row_stop_the_probe(tmp_path):
    api = FakeAPI((422, {"detail": "bad"}))  # not retryable: one request per call

    result = probe(tmp_path, api, n=50)

    assert len(api.requests) == 3
    assert result["stopped"].startswith("3 errors in a row") and "TypeSafeUnprocessableEntityError" in result["stopped"]
    assert (result["ok"], result["errors"]) == (0, 3)


def test_errors_that_are_not_in_a_row_do_not_stop_it(tmp_path):
    api = FakeAPI(*[(422, {"detail": "bad"}), (200, good())] * 5)

    result = probe(tmp_path, api, n=10)

    assert result["calls_made"] == 10 and result["stopped"] is None
    assert (result["ok"], result["errors"]) == (5, 5)


def test_reaching_the_cap_stops_it_and_writes_no_skipped_rows(tmp_path):
    api = FakeAPI((200, good(cost=0.00006)))

    result = probe(tmp_path, api, n=10, cap_usd=0.0001)

    assert len(api.requests) == 2 and len(rows_of(tmp_path)) == 2
    assert result["stopped"].startswith("budget cap reached")
    assert result["calls_made"] == 2 and result["calls_requested"] == 10


def test_a_probe_is_never_overwritten(tmp_path):
    probe(tmp_path, FakeAPI((200, good())), n=1)
    folder = tmp_path / f"latency-20261006T093000Z-{MACHINE}"
    before = (folder / "decisions.jsonl").read_text()

    with pytest.raises(FileExistsError):
        probe(tmp_path, FakeAPI((200, good())), n=1)  # the same second and machine

    assert (folder / "decisions.jsonl").read_text() == before
