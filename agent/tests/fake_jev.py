"""A scripted stand-in for the Jev API over httpx2.MockTransport, shared by the tests that call
JevClient. Nothing here touches the network."""

import asyncio
import json

import httpx2
from typesafe_sdk import Choice, RetryPolicy

from kube_agent.jev_client import EXPECTED_MODEL, JevClient, JevResult

KEY = "sk-or-v1-" + "ab12" * 16
STATE = {"player": {"health": "high", "weapon": "ready"}, "threats": {"remaining": 3}}
QUESTIONS = {
    "tactic": Choice(
        instructions="Which tactic should the player use now?",
        criteria={"ENGAGE": "stand and shoot", "KITE": "back away shooting", "RETREAT": "run", "SEARCH": "go and look"},
    )
}
PROBABILITIES = {"ENGAGE": 0.05, "KITE": 0.9, "RETREAT": 0.03, "SEARCH": 0.02}
GUARD_SECONDS = 20
# Short waits so the retries do not slow the tests, but the same shape as the real policy.
FAST_RETRY = RetryPolicy(max_retries=2, backoff_initial=0.01, backoff_max=0.02, backoff_jitter=0.0, timeout=3.0)


def good(model=EXPECTED_MODEL, cost=0.000054, tokens=1300, choice="KITE", confidence=0.82):
    usage = {"input_tokens": tokens, "output_tokens": 40}
    if cost is not None:
        usage["cost"] = cost
    return {
        "model": model,
        "answers": {"tactic": {"type": "choice", "choice": choice, "confidence": confidence, "probabilities": PROBABILITIES}},
        "usage": usage,
    }


class FakeAPI:
    """A scripted API. Request n gets entry n of the script; the last entry repeats.

    An entry is (status, json_body) or (status, json_body, headers), or a function of the request
    that returns an httpx2.Response or raises.
    """

    def __init__(self, *script):
        self.script, self.requests = list(script), []

    def __call__(self, request):
        self.requests.append({"url": str(request.url), "auth": request.headers.get("authorization"), "body": json.loads(request.content)})
        entry = self.script[min(len(self.requests), len(self.script)) - 1]
        if callable(entry):
            return entry(request)
        status, body, *headers = entry
        return httpx2.Response(status, json=body, headers=headers[0] if headers else None)


class SlowAPI:
    def __init__(self, delay, body=None):
        self.delay, self.body, self.requests = delay, body or good(), 0

    async def __call__(self, request):
        self.requests += 1
        await asyncio.sleep(self.delay)
        return httpx2.Response(200, json=self.body)


def client_for(api, cap_usd=1.0, retry=FAST_RETRY, **kwargs):
    return JevClient(KEY, cap_usd=cap_usd, retry=retry, transport=httpx2.MockTransport(api), **kwargs)


def jev_result(choice="KITE", confidence=0.8, error=None, cost=0.00003, model=EXPECTED_MODEL, tokens=743, latency_ms=300):
    """A JevResult as JevClient.ask returns it: an answer, or (with `error`) a failed call."""
    if error is not None:
        return JevResult(answers=None, model=None, input_tokens=0, cost=0.0, cost_source=None,
                         latency_ms=latency_ms, request_id=None, error=error)
    answers = {"tactic": {"type": "choice", "choice": choice, "confidence": confidence, "probabilities": PROBABILITIES}}
    return JevResult(answers=answers, model=model, input_tokens=tokens, cost=cost, cost_source="usage.cost",
                     latency_ms=latency_ms, request_id=None, error=None)


class FakeClient:
    """Stands in for JevClient in the policy tests: each request waits until the test releases it."""

    expected_model = EXPECTED_MODEL

    def __init__(self):
        self.calls = []  # one dict per request: state, questions, gate, result
        self.exhausted = False
        self.spent = 0.0
        self.cap_usd = 1.0

    async def ask(self, state, questions):
        call = {"state": state, "questions": questions, "gate": asyncio.Event(), "result": None}
        self.calls.append(call)
        await call["gate"].wait()
        return call["result"]

    def release(self, index=-1, result=None, exhaust=False, **answer):
        """Let a request answer. `exhaust` makes this the call that reaches the cap, as the real one does."""
        call = self.calls[index]
        call["result"] = result or jev_result(**answer)
        if exhaust:
            self.spent += call["result"].cost
            self.exhausted = True
        call["gate"].set()


class AutoClient(FakeClient):
    """Answers every request at once, with the same answer."""

    def __init__(self, **answer):
        super().__init__()
        self.answer = answer

    async def ask(self, state, questions):
        self.calls.append({"state": state, "questions": questions})
        return jev_result(**self.answer)
