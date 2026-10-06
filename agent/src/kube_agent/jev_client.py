"""The Jev client: a pinned model through OpenRouter, the cost and the request id read defensively,
every wait bounded in time, and a cap on what a run may spend.

What is known about the SDK is in specs/002-jev-agent/plan.md ("SDK facts", "Key", "Budget
ledger"). An API failure never reaches the caller as an exception: it comes back as a JevResult
whose `error` says what happened, so a failing network cannot end an episode (FR8). A cancellation
is not a failure and is passed on, because the policy cancels a request that went stale.
"""

import asyncio
import logging
import math
import os
import time
from collections.abc import Mapping
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from typesafe_sdk import AsyncTypeSafeClient, RetryPolicy, TypeSafeError

from kube_agent.config import RUNS_DIR
from kube_agent.ledger import BudgetExhausted, require_budget

__all__ = ["BudgetExhausted", "JevClient", "JevResult", "KeyMissing"]

logger = logging.getLogger("kube_agent.jev")

BASE_URL = "https://openrouter.ai/api"
MODEL = "typesafe/jev-1.13"  # the pinned alias; never jev-latest, which moves when a release ships
EXPECTED_MODEL = "typesafe/jev-1.13-20260917"  # the versioned model OpenRouter answers it with
KEY_VARIABLE = "OPENROUTER_API_KEY"
INPUT_USD_PER_MTOK = 0.042  # dollars per million input tokens; output is free (docs, /models)

# Time. The SDK's retry budget is for the whole call and is only checked between attempts, so it
# cannot cut an attempt in flight; the SDK's own timeout applies to each phase of the connection
# (connect, write, read), not to the attempt. Only asyncio.timeout bounds the call for sure.
ATTEMPT_TIMEOUT = 1.5  # seconds, for each phase of one attempt
HARD_LIMIT = 4.0  # seconds, for the whole call: a late answer would be stale anyway
DEFAULT_RETRY = RetryPolicy(max_retries=2, backoff_initial=0.2, backoff_max=1.0, timeout=3.0)

MAX_ERROR_CHARS = 300


class KeyMissing(Exception):
    """The OpenRouter key is not in the environment. The message names the variable, never a value."""


@dataclass(frozen=True)
class JevResult:
    """What one call came to. It is the part of a decisions.jsonl row that Jev is responsible for."""

    answers: dict[str, Any] | None  # per question id, as the API sent them: choice, confidence, probabilities
    model: str | None  # the versioned model that answered
    input_tokens: int
    cost: float  # dollars charged for this call
    cost_source: str | None  # "usage.cost" (OpenRouter's own figure) or "price_per_token" (an estimate); None if no answer
    latency_ms: int  # the whole call, retries included
    request_id: str | None  # the x-typesafe-request-id header, which OpenRouter does not send
    error: str | None  # None unless the call failed or was not made

    def to_row(self) -> dict[str, Any]:
        return asdict(self)


class JevClient:
    """One client for one run. Use it as `async with JevClient.from_environment(...) as jev:`."""

    def __init__(
        self,
        api_key: str,
        *,
        cap_usd: float,
        model: str = MODEL,
        base_url: str = BASE_URL,
        expected_model: str = EXPECTED_MODEL,
        retry: RetryPolicy = DEFAULT_RETRY,
        transport=None,
    ) -> None:
        self.cap_usd = cap_usd
        self.spent = 0.0
        self.model = model
        self.expected_model = expected_model
        self._api_key = api_key
        self._warned_models: set[str] = set()
        self._cap_announced = False
        self._client = AsyncTypeSafeClient(
            api_key=api_key, base_url=base_url, model=model, timeout=ATTEMPT_TIMEOUT, retry=retry, transport=transport
        )

    @classmethod
    def from_environment(
        cls, *, cap_usd: float, runs_dir: Path = RUNS_DIR, environ: Mapping[str, str] | None = None, **kwargs
    ) -> "JevClient":
        """A client that reads the key from the environment, never from a file, and refuses to
        start once the ledger has reached the total. Its cap is the smaller of `cap_usd` and
        what the ledger has left."""
        environ = os.environ if environ is None else environ
        key = (environ.get(KEY_VARIABLE) or "").strip()
        if not key:
            raise KeyMissing(
                f"{KEY_VARIABLE} is not set: load it into this command's environment "
                "(START_HERE.md, 'Key'). It is not read from a file here."
            )
        ledger = require_budget(runs_dir)
        return cls(key, cap_usd=min(cap_usd, ledger.remaining), **kwargs)

    def __repr__(self) -> str:
        return f"JevClient(model={self.model!r}, cap_usd={self.cap_usd}, spent={self.spent})"

    @property
    def exhausted(self) -> bool:
        return self.spent >= self.cap_usd

    async def __aenter__(self) -> "JevClient":
        return self

    async def __aexit__(self, *exception_info) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def ask(self, state: Any, questions: Mapping[str, Any]) -> JevResult:
        """One request to Jev: retried with backoff inside the budget of time, never raising for an
        API failure. At most one should be in flight at a time, so the cap can be passed by at
        most the cost of that one call."""
        if self.exhausted:
            self._announce_cap()
            return self._failure(f"{self._cap_summary()}; no call was made", started=None)
        started = time.monotonic()
        try:
            async with asyncio.timeout(HARD_LIMIT):
                response = await self._client.system_one(state, questions)
        except TimeoutError:
            return self._failure(f"TimeoutError: no answer within {HARD_LIMIT} s", started)
        except TypeSafeError as error:
            return self._failure(f"{type(error).__name__}: {error}", started)
        return self._answer(response, started)

    def _answer(self, response, started: float) -> JevResult:
        http = response.raw_http_response
        raw = http.json()
        input_tokens = response.usage.input_tokens
        cost, cost_source = _cost(raw.get("usage"), input_tokens)
        self.spent += cost
        self._warn_if_unexpected(response.model)
        if self.exhausted:
            self._announce_cap()
        return JevResult(
            answers=raw.get("answers"),
            model=response.model,
            input_tokens=input_tokens,
            cost=cost,
            cost_source=cost_source,
            latency_ms=_milliseconds_since(started),
            # SystemOneResponse.request_id raises when the header is missing, and OpenRouter omits it
            request_id=http.headers.get("x-typesafe-request-id"),
            error=None,
        )

    def _failure(self, message: str, started: float | None) -> JevResult:
        return JevResult(
            answers=None,
            model=None,
            input_tokens=0,
            cost=0.0,
            cost_source=None,
            latency_ms=0 if started is None else _milliseconds_since(started),
            request_id=None,
            error=self._clean(message),
        )

    def _clean(self, text: str) -> str:
        # The SDK's error text includes the body the server sent, which could repeat the key.
        return text.replace(self._api_key, "[key]")[:MAX_ERROR_CHARS]

    def _warn_if_unexpected(self, answering_model: str) -> None:
        if answering_model != self.expected_model and answering_model not in self._warned_models:
            self._warned_models.add(answering_model)
            logger.warning(
                "answering model %r is not the expected %r: the alias or the gateway has moved, "
                "so a threshold tuned on the old model may not hold",
                answering_model, self.expected_model,
            )

    def _cap_summary(self) -> str:
        return f"budget cap reached: ${self.spent:.6f} spent of the ${self.cap_usd:.6f} cap for this run"

    def _announce_cap(self) -> None:
        if not self._cap_announced:
            self._cap_announced = True
            logger.warning("%s; no more calls to Jev in this run", self._cap_summary())


def _cost(usage: Any, input_tokens: int) -> tuple[float, str]:
    """(dollars, where they come from). OpenRouter sends usage.cost and the SDK drops it, so it is
    read from the raw JSON. Without a usable one, the price per input token stands in."""
    cost = usage.get("cost") if isinstance(usage, dict) else None
    if isinstance(cost, (int, float)) and not isinstance(cost, bool) and math.isfinite(cost) and cost >= 0:
        return float(cost), "usage.cost"
    return input_tokens * INPUT_USD_PER_MTOK / 1_000_000, "price_per_token"


def _milliseconds_since(started: float) -> int:
    return round((time.monotonic() - started) * 1000)
