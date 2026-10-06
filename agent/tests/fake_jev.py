"""A scripted stand-in for the Jev API over httpx2.MockTransport, shared by the tests that call
JevClient. Nothing here touches the network."""

import asyncio
import json

import httpx2
from typesafe_sdk import Choice, RetryPolicy

from kube_agent.jev_client import EXPECTED_MODEL, JevClient

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
