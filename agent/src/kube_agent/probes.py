"""Probes that spend money to learn something about Jev. The first one measures how long a call takes.

A probe writes a folder under agent/runs/ with a decisions.jsonl, so the spend ledger counts it,
and a result.json with the summary. It stops by itself, on purpose, when anything is odd: a model
that is not the expected one, errors in a row, or the spending cap.
"""

import json
import math
import platform
import statistics
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from kube_agent.config import REPO_ROOT, RUNS_DIR, config_sha256
from kube_agent.episode import write_row
from kube_agent.features import HpHistory, semantic_state
from kube_agent.jev_client import JevClient

LATENCY_FIXTURE = REPO_ROOT / "agent" / "tests" / "fixtures" / "idle_seed7.jsonl"
LATENCY_FRAME = 200  # t = 1.79 s of idle_seed7: a grunt close and in view, with room behind
ERRORS_IN_A_ROW_LIMIT = 3


def fixture_state(path: Path = LATENCY_FIXTURE, frame: int = LATENCY_FRAME) -> dict:
    """The semantic state of one recorded observation, as the policy would build it."""
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    game_map, observations = rows[0]["map"], rows[1:]
    if not 1 <= frame <= len(observations):
        raise ValueError(f"frame {frame} is outside the {len(observations)} observations of {path}")
    history = HpHistory()
    for obs in observations[: frame - 1]:
        history.add(obs)
    return semantic_state(observations[frame - 1], game_map, history, "ENGAGE")


def percentile(values: list[float], q: float) -> float:
    """The nearest-rank percentile: the value at position ceil(q * n) of the sorted list."""
    ordered = sorted(values)
    return ordered[max(0, math.ceil(q * len(ordered)) - 1)]


def summarize_latency(rows: list[dict], requested: int, stopped: str | None) -> dict:
    """The numbers of a probe. Latency, tokens and cost per call are over the answered calls only."""
    answered = [row for row in rows if row["error"] is None]
    latencies = [row["latency_ms"] for row in answered]
    return {
        "calls_requested": requested,
        "calls_made": len(rows),
        "ok": len(answered),
        "errors": len(rows) - len(answered),
        "models": dict(Counter(row["model"] for row in answered)),
        "latency_ms": {
            "p50": percentile(latencies, 0.5),
            "p95": percentile(latencies, 0.95),
            "min": min(latencies),
            "max": max(latencies),
            "mean": round(statistics.fmean(latencies), 1),
        } if latencies else None,
        "input_tokens_per_call": statistics.fmean(row["input_tokens"] for row in answered) if answered else None,
        "cost_per_call_usd": statistics.fmean(row["cost"] for row in answered) if answered else None,
        "cost_sources": dict(Counter(row["cost_source"] for row in answered)),
        "spend_usd": math.fsum(row["cost"] for row in rows),
        "stopped": stopped,
    }


async def run_latency(
    client: JevClient,
    state: Any,
    questions: Mapping[str, Any],
    n: int,
    runs_dir: Path = RUNS_DIR,
    utc_now=None,
) -> dict:
    """Send the same request `n` times, one after the other, and write the probe's folder.

    It stops early, and says why in `stopped`, when the cap is reached, when a model other than the
    expected one answers (stop and tell the owner), or after ERRORS_IN_A_ROW_LIMIT errors in a row.
    Every call that was made has its row, so the ledger never loses a paid call.
    """
    started = (utc_now or (lambda: datetime.now(timezone.utc)))()
    machine = platform.system().lower()
    run_id = f"latency-{started:%Y%m%dT%H%M%SZ}-{machine}"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True)  # FileExistsError if it is there: a probe is never overwritten

    rows: list[dict] = []
    stopped, errors_in_a_row = None, 0
    with (run_dir / "decisions.jsonl").open("w") as decisions:
        for call in range(1, n + 1):
            if client.exhausted:
                stopped = f"budget cap reached: ${client.spent:.6f} spent of the ${client.cap_usd:.6f} cap"
                break
            result = await client.ask(state, questions)
            row = {"call": call, "state": state, **result.to_row()}
            write_row(decisions, row)
            rows.append(row)
            if result.error is not None:
                errors_in_a_row += 1
                if errors_in_a_row >= ERRORS_IN_A_ROW_LIMIT:
                    stopped = f"{ERRORS_IN_A_ROW_LIMIT} errors in a row, the last: {result.error}"
                    break
                continue
            errors_in_a_row = 0
            if result.model != client.expected_model:
                stopped = f"unexpected model: {result.model!r} answered and {client.expected_model!r} was expected"
                break

    summary = {
        "kind": "latency",
        "run_id": run_id,
        "machine": machine,
        "config_sha256": config_sha256(),
        "pinned_model": client.model,
        "expected_model": client.expected_model,
        "cap_usd": client.cap_usd,
        **summarize_latency(rows, n, stopped),
    }
    (run_dir / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary


def describe_latency(result: dict) -> str:
    """The one line `kube-agent latency` ends with."""
    head = f"latency: {result['calls_made']} calls ({result['ok']} ok, {result['errors']} errors)"
    tail = f"${result['spend_usd']:.6f} in all"
    if result["latency_ms"] is None:
        return f"{head} | no call was answered | {tail} | [{result['run_id']}]"
    latency = result["latency_ms"]
    return (
        f"{head} | p50 {latency['p50']} ms, p95 {latency['p95']} ms, max {latency['max']} ms | "
        f"{result['input_tokens_per_call']:.0f} input tokens and ${result['cost_per_call_usd']:.6f} per call | "
        f"{tail} | cost from {', '.join(result['cost_sources'])} | model {', '.join(result['models'])} | "
        f"[{result['run_id']}]"
    )
