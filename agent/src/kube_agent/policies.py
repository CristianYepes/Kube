"""The players that choose the tactic: idle (none) and scripted (four rules). Jev joins later.

A policy sees every observation through step() and answers with a decision row when it decided
on that observation, else None. Its `tactic` is the one in force, and the controller turns it
into keys. The row is what decisions.jsonl stores for every policy (plan.md, "Logs").
"""

from kube_agent.features import HpHistory, health_band, semantic_state

INITIAL_TACTIC = "ENGAGE"  # in force until a policy's first decision
DECISION_INTERVAL = 0.5  # seconds of game time between decisions
HEALTH_RANK = {"low": 0, "medium": 1, "high": 2}


class DecisionSchedule:
    """When a decision is due: every 0.5 s since the last one, and at once on an event.

    The events are a new wave and health dropping a band, each seen against the previous
    observation. Jev's policy will use the same schedule, so the players differ in who chooses
    and not in how often.
    """

    def __init__(self) -> None:
        self._last_decision: float | None = None
        self._wave: int | None = None
        self._rank: int | None = None

    def due(self, obs: dict) -> bool:
        """Call once per observation. A True answer starts the next 0.5 s."""
        rank = HEALTH_RANK[health_band(obs["hp"])]
        new_wave = self._wave is not None and obs["wave"] > self._wave
        health_drop = self._rank is not None and rank < self._rank
        self._wave, self._rank = obs["wave"], rank

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
