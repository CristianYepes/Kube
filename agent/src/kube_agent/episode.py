"""One episode: play the game under a policy, keep the logs and the result.

The logs are those of specs/002-jev-agent/plan.md ("Logs"): a folder per episode under
agent/runs/ with result.json, episode.jsonl and decisions.jsonl. They are committed, so a run
is never overwritten or deleted.
"""

import asyncio
import contextlib
import hashlib
import json
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

from kube_agent.bridge import BridgeError, GameBridge, game_command
from kube_agent.config import DEFAULT_RUN_BUDGET_USD, REPO_ROOT, RUNS_DIR, config_sha256
from kube_agent.controller import Controller
from kube_agent.jev_client import JevClient
from kube_agent.policies import POLICIES, make_policy

STALL_SECONDS = 0.1  # a gap above this between two observations handled is a stall (AC8)
ROW_INTERVAL = 0.5  # seconds of game time between rows of episode.jsonl
GUARD_FACTOR = 2.0  # wall-clock seconds allowed per game second, plus GUARD_SLACK, before giving up
GUARD_SLACK = 30.0
OUTCOMES = {1: "lose", 2: "win"}  # the game's `state`: 0 playing, 1 game over, 2 won


class StallCounter:
    """Counts the gaps above STALL_SECONDS between observations, on the host's monotonic clock.

    The game's own clock cannot show them: the game never waits, and the pipe holds the lines
    it wrote meanwhile.
    """

    def __init__(self, clock=time.monotonic) -> None:
        self._clock = clock
        self._last: float | None = None
        self.count = 0

    def tick(self) -> None:
        """Call at the start of handling each observation."""
        now = self._clock()
        if self._last is not None and now - self._last > STALL_SECONDS:
            self.count += 1
        self._last = now


class Tally:
    """What an episode did, observation by observation."""

    def __init__(self) -> None:
        self.survival = 0.0
        self.wave = 0
        self.kills = 0
        self.damage = 0
        self.drops = 0
        self.tactic_seconds: dict[str, float] = {}
        self.decisions = 0
        self.applied = 0
        self.switches = 0
        self.spend = 0.0
        self._last: dict | None = None

    def observe(self, obs: dict, tactic: str | None) -> None:
        """`tactic` is the one in force while this observation's frame was played."""
        last = self._last
        if last is not None:
            # The game lets hp fall below zero; the damage cannot exceed the hp there was.
            self.damage += max(0, max(last["hp"], 0) - max(obs["hp"], 0))
            if obs["wave"] == last["wave"]:
                self.kills += max(0, len(last["enemies"]) - len(obs["enemies"]))
            elif obs["wave"] > last["wave"]:
                # The game starts the next wave only when none is left (check_wave_advance), so
                # every enemy seen on the last frame died on this one.
                self.kills += len(last["enemies"])
        self.survival = obs["t"]
        self.wave = max(self.wave, obs["wave"])
        self.drops = obs["drops"]
        if tactic is not None:
            self.tactic_seconds[tactic] = self.tactic_seconds.get(tactic, 0.0) + obs["dt"]
        self._last = obs

    def decision(self, row: dict) -> None:
        self.decisions += 1
        self.applied += bool(row["applied"])
        if row["applied"] and row["tactic"] != row["state"]["current_tactic"]:
            self.switches += 1
        self.spend += row.get("cost", 0.0)


def _episode_row(obs: dict, tactic: str | None) -> dict:
    player = obs["player"]
    return {
        "t": round(obs["t"], 2), "x": round(player["x"], 2), "y": round(player["y"], 2),
        "hp": obs["hp"], "wave": obs["wave"], "enemies": len(obs["enemies"]), "tactic": tactic,
    }


def write_row(file, row: dict) -> None:
    file.write(json.dumps(row) + "\n")
    file.flush()  # an episode that dies half way still leaves what it did


async def play(game, policy, controller, episode_file, decisions_file, max_seconds: float) -> dict:
    """Play one episode on a started game and return its numbers.

    It ends on the first observation with `state != 0` (the game is won or lost) or with a game
    clock at `max_seconds`. The policy is always closed, which returns the rows of whatever it
    still had pending. The caller closes the game, which sends Q.
    """
    stalls = StallCounter()
    tally = Tally()
    next_row_at, last_row_t, last, outcome = 0.0, None, None, None
    try:
        async with contextlib.aclosing(game.observations()) as observations:
            async for obs in observations:
                stalls.tick()
                tactic = policy.tactic
                tally.observe(obs, tactic)
                if obs["t"] >= next_row_at:
                    write_row(episode_file, _episode_row(obs, tactic))
                    next_row_at, last_row_t = obs["t"] + ROW_INTERVAL, obs["t"]
                last = obs
                if obs["state"] != 0:
                    outcome = OUTCOMES.get(obs["state"])
                    if outcome is None:
                        raise BridgeError(f"unknown game state {obs['state']} in frame {obs['frame']}")
                    break
                if obs["t"] >= max_seconds:
                    outcome = "timeout"
                    break

                decision = policy.step(obs)
                if decision:
                    write_row(decisions_file, decision)
                    tally.decision(decision)
                if policy.tactic is not None:
                    line = controller.command(obs, policy.tactic)
                    if line is not None:
                        await game.send(line)
    finally:  # a request still out when the episode ends has its answer, and its cost, recorded
        for decision in await policy.aclose():
            write_row(decisions_file, decision)
            tally.decision(decision)

    if outcome is None:
        where = f"t={last['t']}" if last else "the first observation"
        raise BridgeError(f"the game's output ended at {where}, before the episode did")
    if last_row_t != last["t"]:  # the path ends where the episode ended
        write_row(episode_file, _episode_row(last, policy.tactic))
    return {
        "outcome": outcome,
        "survival_seconds": round(tally.survival, 2),
        "wave_reached": tally.wave,
        "kills": tally.kills,
        "damage_taken": tally.damage,
        "drops": tally.drops,
        "stalls": stalls.count,
        "tactic_seconds": {name: round(seconds, 2) for name, seconds in tally.tactic_seconds.items()},
        "switches": tally.switches,
        "decisions": tally.decisions,
        "decisions_applied": tally.applied,
        "spend_usd": round(tally.spend, 6),
    }


async def _play_through(command, policy_name, episode_file, decisions_file, max_seconds, jev_client=None):
    limit = max_seconds * GUARD_FACTOR + GUARD_SLACK
    async with GameBridge(command) as game:
        game_map = game.init["map"]
        policy = make_policy(policy_name, game_map, jev_client=jev_client)
        try:
            async with asyncio.timeout(limit):
                return await play(game, policy, Controller(game_map), episode_file, decisions_file, max_seconds)
        except TimeoutError:
            raise BridgeError(
                f"the episode did not finish within {limit} s of wall-clock time for {max_seconds} s of game"
            ) from None


async def run_episode(
    policy_name: str,
    seed: int,
    map_path: str,
    runner: str,
    max_seconds: float,
    runs_dir: Path = RUNS_DIR,
    utc_now=None,
    command: list[str] | None = None,
    budget_usd: float = DEFAULT_RUN_BUDGET_USD,
    jev_client=None,
    environ=None,
    ledger_dir: Path | None = None,
) -> dict:
    """Play one episode, write its folder under runs_dir and return result.json's content.

    For the Jev policy `budget_usd` caps what the run may spend (the ledger's remainder caps it too).
    The ledger is read from `ledger_dir`, which is `runs_dir` unless the caller says otherwise: an evaluation plays
    its episodes in a folder of its own and passes agent/runs, because the $1 budget is the spend of the whole tree.
    `utc_now`, `command`, `jev_client` and `environ` exist for the tests: a fixed clock, a
    stand-in for the game, a client over a fake transport and a fake environment.
    """
    if policy_name not in POLICIES:
        raise ValueError(f"unknown policy {policy_name!r}: expected one of {POLICIES}")
    map_sha256 = hashlib.sha256((REPO_ROOT / map_path).read_bytes()).hexdigest()  # fails before any folder exists
    owns_client = policy_name == "jev" and jev_client is None
    if owns_client:  # no key, or no budget left, stops here, before a folder exists
        jev_client = JevClient.from_environment(cap_usd=budget_usd, runs_dir=ledger_dir or runs_dir, environ=environ)
    try:
        return await _run_in_folder(
            policy_name=policy_name, seed=seed, map_path=map_path, runner=runner, max_seconds=max_seconds,
            runs_dir=runs_dir, utc_now=utc_now, command=command, map_sha256=map_sha256, jev_client=jev_client)
    finally:
        if owns_client:
            await jev_client.aclose()


async def _run_in_folder(*, policy_name, seed, map_path, runner, max_seconds, runs_dir, utc_now, command, map_sha256, jev_client):
    machine = platform.system().lower()
    started = (utc_now or (lambda: datetime.now(timezone.utc)))()
    run_id = f"{started:%Y%m%dT%H%M%SZ}-{policy_name}-s{seed}-{machine}"
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True)  # FileExistsError if it is there: a run is never overwritten

    result = {
        "run_id": run_id, "policy": policy_name, "seed": seed, "map": map_path,
        "map_sha256": map_sha256, "machine": machine, "runner": runner,
        "config_sha256": config_sha256(), "max_seconds": max_seconds,
    }
    if jev_client is not None:
        result["budget_usd"] = jev_client.cap_usd
    command = command or game_command(runner, map_path, seed)
    with (run_dir / "episode.jsonl").open("w") as episode_file, (run_dir / "decisions.jsonl").open("w") as decisions_file:
        try:
            result.update(
                await _play_through(command, policy_name, episode_file, decisions_file, max_seconds, jev_client))
        except Exception as error:
            result.update(outcome="error", error=f"{type(error).__name__}: {error}")
            _write_result(run_dir, result)
            raise
    _write_result(run_dir, result)
    return result


def _write_result(run_dir: Path, result: dict) -> None:
    (run_dir / "result.json").write_text(json.dumps(result, indent=2) + "\n")


def summarize(result: dict) -> str:
    """The one line `kube-agent run` ends with."""
    return (
        f"{result['policy']} s{result['seed']}: {result['outcome']} after {result['survival_seconds']:.1f} s "
        f"(wave {result['wave_reached']}, {result['kills']} kills), {result['decisions']} decisions, "
        f"{result['decisions_applied']} applied, spend ${result['spend_usd']:.4f}  [{result['run_id']}]"
    )
