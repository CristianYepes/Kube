"""The players that choose the tactic: idle (none), scripted (four rules) and Jev.

A policy sees every observation through step() and answers with a decision row when it decided on
that observation, else None. Its `tactic` is the one in force, and the controller turns it into
keys. The row is what decisions.jsonl stores for every policy (plan.md, "Logs"). `aclose()` is
called when the episode ends and returns the rows of anything still pending.
"""

import asyncio
import logging
from dataclasses import dataclass

from kube_agent.config import CONFIDENCE_THRESHOLD, DECISION_INTERVAL, questions
from kube_agent.controller import TACTICS
from kube_agent.features import HpHistory, health_band, semantic_state
from kube_agent.jev_client import HARD_LIMIT

logger = logging.getLogger("kube_agent.jev")

INITIAL_TACTIC = "ENGAGE"  # in force until a policy's first decision
POLICIES = ("idle", "scripted", "jev")
HEALTH_RANK = {"low": 0, "medium": 1, "high": 2}


class DecisionSchedule:
    """When a decision is due: every 0.5 s since the last one, and at once on an event.

    The events are a new wave and health dropping a band, each seen against the previous
    observation. Scripted and Jev share this schedule, so the players differ in who chooses and
    not in how often. After each call `last_event` says which event made it due, if one did.
    """

    def __init__(self) -> None:
        self._last_decision: float | None = None
        self._wave: int | None = None
        self._rank: int | None = None
        self.last_event: str | None = None

    def due(self, obs: dict) -> bool:
        """Call once per observation. A True answer starts the next 0.5 s."""
        rank = HEALTH_RANK[health_band(obs["hp"])]
        new_wave = self._wave is not None and obs["wave"] > self._wave
        health_drop = self._rank is not None and rank < self._rank
        self._wave, self._rank = obs["wave"], rank
        self.last_event = "new_wave" if new_wave else "health_drop" if health_drop else None

        on_time = self._last_decision is None or obs["t"] - self._last_decision >= DECISION_INTERVAL
        decide = on_time or new_wave or health_drop
        if decide:
            self._last_decision = obs["t"]
        return decide


def scripted_tactic(state: dict) -> str:
    """The baseline's four rules, in order, over the same state Jev reads."""
    close = state["threats"]["close_count"] > 0
    if close and state["player"]["health"] == "low":
        return "RETREAT"
    if close:
        return "KITE"
    if state["threats"]["in_view"] > 0:
        return "ENGAGE"
    return "SEARCH"


class IdlePolicy:
    """Does nothing. With no tactic the episode sends the game no command at all."""

    tactic = None

    def step(self, obs: dict) -> None:
        return None

    async def aclose(self) -> list[dict]:
        return []


class ScriptedPolicy:
    """Four fixed rules, applied on Jev's schedule."""

    def __init__(self, game_map: list[str]) -> None:
        self.tactic = INITIAL_TACTIC
        self._map = game_map
        self._history = HpHistory()  # fed on every observation: being_hit looks a second back
        self._schedule = DecisionSchedule()

    def step(self, obs: dict) -> dict | None:
        self._history.add(obs)
        if not self._schedule.due(obs):
            return None
        state = semantic_state(obs, self._map, self._history, self.tactic)
        self.tactic = scripted_tactic(state)
        return {"t": obs["t"], "state": state, "tactic": self.tactic, "applied": True}

    async def aclose(self) -> list[dict]:
        return []


@dataclass
class _InFlight:
    task: asyncio.Task
    state: dict  # what was sent
    sent_at: float  # the game clock of the observation the state came from
    stale: bool = False  # an event happened after the state was sent


class JevPolicy:
    """Jev picks the tactic every 0.5 s and on events; the code does the rest (plan.md, "Jev policy").

    One request at a time. It runs as a task, and step() only looks at whether it has finished, so
    the game loop never waits for Jev (FR8). An answer is applied when its confidence reaches the
    threshold and it is not stale, that is, no event happened after its state was sent. When the
    budget is spent the scripted rules take over for good.
    """

    def __init__(self, game_map: list[str], client, threshold: float = CONFIDENCE_THRESHOLD,
                 close_wait: float = HARD_LIMIT + 1.0) -> None:
        self.tactic = INITIAL_TACTIC
        self._map = game_map
        self._client = client
        self._threshold = threshold
        self._close_wait = close_wait
        self._history = HpHistory()
        self._schedule = DecisionSchedule()
        self._in_flight: _InFlight | None = None
        self._owed = False  # a decision is due and no request has gone out for it
        self._fallback = False  # the budget is spent: the rules decide from now on

    def step(self, obs: dict) -> dict | None:
        self._history.add(obs)
        if self._schedule.due(obs):
            self._owed = True
            if self._schedule.last_event and self._in_flight is not None:
                self._in_flight.stale = True  # noted before the answer is read: same-frame events count

        row = None
        if self._in_flight is not None and self._in_flight.task.done():
            flight, self._in_flight = self._in_flight, None
            row = self._row_for(flight, answered_at=obs["t"])
        if not self._fallback and self._client.exhausted:
            self._fallback = True
            logger.warning(
                "budget cap reached ($%.6f spent of the $%.6f cap): the scripted rules choose the tactic from now on",
                self._client.spent, self._client.cap_usd,
            )

        if self._owed:
            if self._fallback:
                if row is None:  # at most one row per step; the decision waits for the next one
                    row = self._decide_by_the_rules(obs)
                    self._owed = False
            elif self._in_flight is None:
                self._send(obs)
                self._owed = False
        return row

    async def aclose(self) -> list[dict]:
        """Wait, for a while, for the request still in flight, so a paid answer is not lost."""
        flight, self._in_flight = self._in_flight, None
        if flight is None:
            return []
        try:
            await asyncio.wait({flight.task}, timeout=self._close_wait)
        except asyncio.CancelledError:
            flight.task.cancel()
            raise
        if not flight.task.done():
            flight.task.cancel()
            await asyncio.gather(flight.task, return_exceptions=True)
            logger.warning(
                "a request to Jev was still in flight when the episode ended and was cancelled: "
                "its cost, if it had one, is not in the ledger"
            )
            return []
        try:
            return [self._row_for(flight, answered_at=None, after_the_end=True)]
        except Exception as error:  # a request that failed in our own code: report it, do not fail the close
            logger.warning("a request to Jev in flight at the end of the episode failed: %r", error)
            return []

    def _send(self, obs: dict) -> None:
        state = semantic_state(obs, self._map, self._history, self.tactic)
        task = asyncio.create_task(self._client.ask(state, questions()))
        self._in_flight = _InFlight(task, state, obs["t"])

    def _decide_by_the_rules(self, obs: dict) -> dict:
        state = semantic_state(obs, self._map, self._history, self.tactic)
        self.tactic = scripted_tactic(state)
        return {
            "t": obs["t"], "state": state, "tactic": self.tactic, "applied": True, "reason": None,
            "source": "scripted_fallback",
        }

    def _row_for(self, flight: _InFlight, answered_at: float | None, after_the_end: bool = False) -> dict:
        """The decision row of a finished request, applying its answer if it deserves it."""
        result = flight.task.result()  # never raises for an API failure; a bug in our own code does
        answer = (result.answers or {}).get("tactic")
        choice = answer.get("choice") if isinstance(answer, dict) else None
        confidence = answer.get("confidence") if isinstance(answer, dict) else None
        usable = (
            result.error is None and choice in TACTICS
            and isinstance(confidence, (int, float)) and not isinstance(confidence, bool)
        )
        if result.error is not None:
            reason = "error"
        elif not usable:
            reason = "malformed"
        elif after_the_end:
            reason = "episode_ended"
        elif self._fallback:
            reason = "fallback"
        elif flight.stale:
            reason = "stale"
        elif confidence < self._threshold:
            reason = "below_threshold"
        else:
            reason = None
        if reason is None:
            self.tactic = choice
        return {
            "t": flight.sent_at,
            "state": flight.state,
            "tactic": choice if usable else None,
            "applied": reason is None,
            "reason": reason,
            "confidence": confidence if usable else None,
            "source": "jev",
            "answered_at": answered_at,
            "stale": flight.stale,
            **result.to_row(),
        }


def make_policy(name: str, game_map: list[str], jev_client=None):
    if name == "idle":
        return IdlePolicy()
    if name == "scripted":
        return ScriptedPolicy(game_map)
    if name == "jev":
        if jev_client is None:
            raise ValueError("the 'jev' policy needs a Jev client")
        return JevPolicy(game_map, jev_client)
    raise ValueError(f"unknown policy {name!r}: expected one of {POLICIES}")
