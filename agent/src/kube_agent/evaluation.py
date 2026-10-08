"""The final evaluation (T9, AC11): idle, scripted and Jev on the test seeds, once, with the frozen config.

`kube-agent eval` plays the episodes one after the other, interleaved by seed so that a slow stretch of the
network or of the machine hits every policy alike (R15 saw one), and writes
agent/runs/eval-<UTC date-time>-<machine>/ with one folder per episode, plan.json, result.json and report.md.

It refuses to start when the config in the code is not the frozen one, and refuses to measure a test seed
that an earlier evaluation already measured: the test seeds are used once (FR12).
"""

import json
import math
import platform
import statistics
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from kube_agent.config import REPO_ROOT, RUNS_DIR, config_sha256
from kube_agent.episode import run_episode as play_episode
from kube_agent.probes import percentile
from kube_agent.stats import wilson_interval

FROZEN_PATH = REPO_ROOT / "agent" / "frozen.json"
TEST_SEEDS_FROM = 101  # seeds 1-20 are development, 101-120 are test (spec.md, Decision 3)
STUCK_SECONDS = 60.0  # a timeout in which nothing changed for this long is marked as stuck
FAILED_IN_A_ROW_LIMIT = 3
WAVES = 3  # the game is won when the third wave is cleared
OUTCOMES = ("win", "lose", "timeout")  # an episode with any other outcome (error) has no result to report
POLICY_ORDER = ("idle", "scripted", "jev")


class EvalRefused(Exception):
    """The evaluation was not started, or not allowed to go on, and the message says why."""


# --- what to play ----------------------------------------------------------------------------------


def parse_seeds(text: str) -> list[int]:
    """Seeds as '101-120', '1,3,7' or '1-3,7,9-10'. A seed named twice is an error."""
    seeds: list[int] = []
    for part in text.split(","):
        pieces = [piece.strip() for piece in part.split("-")]
        try:
            if len(pieces) not in (1, 2):
                raise ValueError
            first, last = int(pieces[0]), int(pieces[-1])
        except ValueError:
            raise ValueError(f"bad seed list {text!r}: {part.strip()!r} is not a seed or a range such as 101-120") from None
        if first < 1 or last < first:
            raise ValueError(f"bad seed list {text!r}: {part.strip()!r} is not a range of seeds from 1 up")
        seeds.extend(range(first, last + 1))
    repeated = sorted({seed for seed in seeds if seeds.count(seed) > 1})
    if repeated:
        raise ValueError(f"bad seed list {text!r}: seed {repeated[0]} is named twice")
    return seeds


def plan_episodes(seeds: list[int], maps: list[str], policies: list[str]) -> list[tuple[int, str, str]]:
    """Seed by seed, and within a seed map by map and policy by policy, so that whatever slows one stretch of the
    run slows every policy and map alike."""
    return [(seed, map_path, policy) for seed in seeds for map_path in maps for policy in policies]


def check_frozen(frozen_path: Path = FROZEN_PATH) -> str:
    """The frozen hash, if it is the hash of the config in the code. Otherwise nothing is evaluated."""
    if not frozen_path.is_file():
        raise EvalRefused(f"no frozen config at {frozen_path}: only a config frozen at the end of T8 is evaluated")
    frozen = json.loads(frozen_path.read_text())["config_sha256"]
    current = config_sha256()
    if frozen != current:
        raise EvalRefused(
            f"the config in the code ({current[:12]}...) is not the frozen config ({frozen[:12]}...) of {frozen_path.name}: "
            "changing the question, theta or the cadence needs a new freeze and the owner's OK"
        )
    return frozen


def _read_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line] if path.is_file() else []


def load_episodes(folder: Path) -> list[dict]:
    """Every episode folder in `folder`: its result, its decision rows and its path rows."""
    return [
        {"result": json.loads(result_path.read_text()), "decisions": _read_rows(result_path.parent / "decisions.jsonl"),
         "episode": _read_rows(result_path.parent / "episode.jsonl")}
        for result_path in sorted(folder.glob("*/result.json"))
    ]


def _key(result: dict) -> tuple[str, str, int]:
    return result["policy"], result["map"], result["seed"]


def refuse_repeated_test_seeds(runs_dir: Path, episodes: list[tuple[int, str, str]], ignore: str | None = None) -> None:
    """A test seed is measured once per policy and map: an earlier evaluation that has a result for one refuses this one.
    `ignore` is the folder being resumed, whose own episodes are not repeats."""
    wanted = {(policy, map_path, seed) for seed, map_path, policy in episodes if seed >= TEST_SEEDS_FROM}
    if not wanted:
        return
    for result_path in sorted(runs_dir.glob("eval-*/*/result.json")):
        folder = result_path.parent.parent
        result = json.loads(result_path.read_text())
        if folder.name != ignore and result.get("outcome") in OUTCOMES and _key(result) in wanted:
            policy, map_path, seed = _key(result)
            raise EvalRefused(
                f"seed {seed} ({policy} on {map_path}) was already measured in {folder.name}: the test seeds are "
                "measured once (--repeat to measure them again)"
            )


# --- the numbers -----------------------------------------------------------------------------------


def stuck_seconds(rows: list[dict]) -> float:
    """For how long, at the end of an episode, neither the player's position nor the enemy count changed."""
    if len(rows) < 2:
        return 0.0
    last = rows[-1]
    since = last["t"]
    for row in reversed(rows):
        if (row["x"], row["y"], row["enemies"]) != (last["x"], last["y"], last["enemies"]):
            break
        since = row["t"]
    return last["t"] - since


def _spread(values: list[float]) -> dict | None:
    if not values:
        return None
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive") if len(values) > 1 else (values[0],) * 3
    return {"median": statistics.median(values), "q1": q1, "q3": q3}


def _shares(seconds: Counter) -> dict:
    total = sum(seconds.values())
    return {tactic: value / total for tactic, value in seconds.items()} if total else {}


def _jev_stats(done: list[dict]) -> dict | None:
    if not any(e["result"]["policy"] == "jev" for e in done):
        return None
    rows = [row for e in done for row in e["decisions"] if row.get("source") == "jev"]
    latencies = [row["latency_ms"] for row in rows if not row.get("error")]
    spend = math.fsum(e["result"]["spend_usd"] for e in done)
    return {
        "spend_total": spend,
        "spend_per_episode": spend / len(done),
        "calls": len(rows),
        "errors": sum(1 for row in rows if row.get("error")),
        "reasons": dict(Counter(row.get("reason") or "applied" for row in rows)),
        "fallback_episodes": sum(any(row.get("source") == "scripted_fallback" for row in e["decisions"]) for e in done),
        "latency_ms": {"p50": percentile(latencies, 0.5), "p95": percentile(latencies, 0.95), "max": max(latencies)} if latencies else None,
    }


def group_stats(episodes: list[dict]) -> dict:
    """The numbers of AC11 for the episodes of one policy on one map."""
    done = [e for e in episodes if e["result"]["outcome"] in OUTCOMES]
    results = [e["result"] for e in done]
    n = len(results)
    outcomes = {outcome: sum(r["outcome"] == outcome for r in results) for outcome in OUTCOMES}
    cleared = [WAVES if r["outcome"] == "win" else max(r["wave_reached"] - 1, 0) for r in results]
    damaged = [r["damage_taken"] for r in results if r["damage_taken"] > 0]
    seconds = {outcome: Counter() for outcome in OUTCOMES}
    for r in results:
        seconds[r["outcome"]].update(r["tactic_seconds"])
    return {
        "n": n,
        "errors": len(episodes) - n,
        "outcomes": outcomes,
        "wins": outcomes["win"],
        "wins_wilson95": list(wilson_interval(outcomes["win"], n)) if n else None,
        "survival": _spread([r["survival_seconds"] for r in results]),
        "time_to_win": _spread([r["survival_seconds"] for r in results if r["outcome"] == "win"]),
        "waves_cleared_mean": statistics.fmean(cleared) if cleared else None,
        "damage": {"episodes": len(damaged), "mean": sum(r["damage_taken"] for r in results) / n if n else 0.0},
        "stalls": sum(r["stalls"] for r in results),
        "tactic_share": {outcome: _shares(seconds[outcome]) for outcome in OUTCOMES},
        "stuck_timeouts": sum(e["result"]["outcome"] == "timeout" and stuck_seconds(e["episode"]) >= STUCK_SECONDS for e in done),
        "jev": _jev_stats(done),
    }


def _sign_test(faster: int, slower: int) -> float:
    """Two-sided exact p-value of the sign test; ties are left out."""
    n = faster + slower
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(max(faster, slower), n + 1)) / 2**n
    return min(1.0, 2 * tail)


def jev_against_scripted(episodes: list[dict]) -> dict | None:
    """Seed by seed, the time to win of Jev minus the time to win of scripted, where both won."""
    by_policy = {policy: {e["result"]["seed"]: e["result"] for e in episodes if e["result"]["policy"] == policy and e["result"]["outcome"] in OUTCOMES}
                 for policy in ("jev", "scripted")}
    seeds = sorted(set(by_policy["jev"]) & set(by_policy["scripted"]))
    if not seeds:
        return None
    both_won = [s for s in seeds if by_policy["jev"][s]["outcome"] == "win" == by_policy["scripted"][s]["outcome"]]
    diffs = [by_policy["jev"][s]["survival_seconds"] - by_policy["scripted"][s]["survival_seconds"] for s in both_won]
    faster, slower = sum(d < 0 for d in diffs), sum(d > 0 for d in diffs)
    return {
        "seeds": len(seeds), "both_won": len(both_won), "faster": faster, "slower": slower, "equal": len(diffs) - faster - slower,
        "median_difference": statistics.median(diffs) if diffs else None, "mean_difference": statistics.fmean(diffs) if diffs else None,
        "sign_test_p": _sign_test(faster, slower),
    }


# --- the report ------------------------------------------------------------------------------------


def _time(spread: dict | None) -> str:
    return f"{spread['median']:.1f} [{spread['q1']:.1f}-{spread['q3']:.1f}]" if spread else "-"


def _share_text(shares: dict) -> str:
    return ", ".join(f"{tactic} {share:.0%}" for tactic, share in sorted(shares.items(), key=lambda item: -item[1])) or "-"


def build_report(episodes: list[dict], plan: dict, run_id: str, frozen_sha: str, current_sha: str, stopped: str | None) -> str:
    planned = {(policy, map_path, seed) for seed, map_path, policy in plan_episodes(plan["seeds"], plan["maps"], plan["policies"])}
    finished = {_key(e["result"]) for e in episodes if e["result"]["outcome"] in OUTCOMES}
    lines = [f"# Final evaluation: {run_id}", ""]
    if stopped or not planned <= finished:
        lines += [f"**INCOMPLETE:** {len(planned & finished)} of {len(planned)} planned episodes have a result."
                  + (f" It stopped because: {stopped}." if stopped else ""), ""]
    same = frozen_sha == current_sha
    lines += [
        f"- config hash: `{current_sha}`; the frozen one is `{frozen_sha}`: "
        + ("it equals the frozen one." if same else "**it DIFFERS from the frozen one: this report does not measure the frozen config.**"),
        f"- seeds: {plan['seeds'][0]}-{plan['seeds'][-1]} ({len(plan['seeds'])}); maps: {', '.join(plan['maps'])}; policies: {', '.join(plan['policies'])}",
        f"- runner: {plan['runner']}; game time limit {plan['max_seconds']:.0f} s per episode; Jev cap ${plan['budget_usd']:.2f} for the evaluation",
        "- generated by `kube-agent eval`; the reading of these numbers is in the research log (R17)",
        "",
    ]
    for map_path in plan["maps"]:
        on_map = [e for e in episodes if e["result"]["map"] == map_path]
        stats = {policy: group_stats([e for e in on_map if e["result"]["policy"] == policy]) for policy in plan["policies"]}
        lines += [f"## {map_path}", "", "### Results per policy", "",
                  "| policy | n | wins | Wilson 95% | lost | timeouts | failed | survival s, median [Q1-Q3] | time to win s, median [Q1-Q3] | waves cleared | with damage | stalls |",
                  "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for policy, s in stats.items():
            wilson = f"{s['wins_wilson95'][0]:.0%}-{s['wins_wilson95'][1]:.0%}" if s["wins_wilson95"] else "-"
            waves = f"{s['waves_cleared_mean']:.2f}" if s["waves_cleared_mean"] is not None else "-"
            lines.append(f"| {policy} | {s['n']} | {s['wins']} | {wilson} | {s['outcomes']['lose']} | {s['outcomes']['timeout']} | {s['errors']} | "
                         f"{_time(s['survival'])} | {_time(s['time_to_win'])} | {waves} | {s['damage']['episodes']} (mean {s['damage']['mean']:.1f}) | {s['stalls']} |")
        lines += ["", "### Share of game time in each tactic", "", "| policy | in wins | in losses | in timeouts |", "|---|---|---|---|"]
        for policy, s in stats.items():
            lines.append(f"| {policy} | {_share_text(s['tactic_share']['win'])} | {_share_text(s['tactic_share']['lose'])} | {_share_text(s['tactic_share']['timeout'])} |")
        stuck = {policy: s["stuck_timeouts"] for policy, s in stats.items() if s["stuck_timeouts"]}
        if stuck:
            lines += ["", f"Timeouts in which nothing changed for the last {STUCK_SECONDS:.0f} s of game time (probably the spawn trap of R15; "
                          f"read episode.jsonl to confirm): {', '.join(f'{p} {n}' for p, n in stuck.items())}."]
        jev = stats.get("jev", {}).get("jev")
        if jev:
            latency = jev["latency_ms"]
            applied = jev["reasons"].get("applied", 0) / jev["calls"] if jev["calls"] else 0.0
            lines += ["", "### Jev", "", "| cost per episode | cost total | calls | applied | errors | episodes that fell back to the rules | latency p50 / p95 / max ms |",
                      "|---|---|---|---|---|---|---|",
                      f"| ${jev['spend_per_episode']:.5f} | ${jev['spend_total']:.5f} | {jev['calls']} | {applied:.0%} | {jev['errors']} | {jev['fallback_episodes']} | "
                      + (f"{latency['p50']} / {latency['p95']} / {latency['max']}" if latency else "-") + " |",
                      "", "What became of its answers: " + ", ".join(f"{reason} {count}" for reason, count in sorted(jev["reasons"].items(), key=lambda item: -item[1])) + "."]
        pair = jev_against_scripted(on_map)
        if pair:
            lines += ["", "### Jev against scripted, same seeds", "",
                      f"On {pair['seeds']} seeds with a result for both, both won on {pair['both_won']}. Time to win, Jev minus scripted: "
                      + (f"median {pair['median_difference']:+.1f} s, mean {pair['mean_difference']:+.1f} s; " if pair["both_won"] else "")
                      + f"Jev faster on {pair['faster']}, slower on {pair['slower']}, equal on {pair['equal']}; sign test, two-sided, p = {pair['sign_test_p']:.3f}."]
        lines.append("")
    return "\n".join(lines)


# --- running it ------------------------------------------------------------------------------------


def _progress(number: int, total: int, seed: int, map_path: str, policy: str, result: dict) -> str:
    return (f"[{number}/{total}] {policy} s{seed} on {map_path}: {result['outcome']} after {result.get('survival_seconds', 0)} s, "
            f"damage {result.get('damage_taken', 0)}, spend ${result.get('spend_usd', 0.0):.4f}")


async def run_evaluation(
    plan: dict | None,
    runs_dir: Path = RUNS_DIR,
    run_episode: Callable = play_episode,
    utc_now: Callable[[], datetime] | None = None,
    say: Callable[[str], None] = lambda line: print(line, flush=True),
    frozen_path: Path = FROZEN_PATH,
    repeat: bool = False,
    resume: str | None = None,
) -> dict:
    """Play every planned episode that has no result yet, then write result.json and report.md, and return the summary.

    `plan` has seeds, maps, policies, runner, max_seconds, budget_usd (for all of Jev's episodes together) and
    per_episode_usd. With `resume` it is read from that folder instead, and only the missing episodes are played.
    """
    frozen = check_frozen(frozen_path)
    if resume:
        eval_dir = runs_dir / resume
        if not (eval_dir / "plan.json").is_file():
            raise EvalRefused(f"{resume} is not an evaluation folder in {runs_dir} (it has no plan.json)")
        plan = json.loads((eval_dir / "plan.json").read_text())
    else:
        started = (utc_now or (lambda: datetime.now(timezone.utc)))()
        eval_dir = runs_dir / f"eval-{started:%Y%m%dT%H%M%SZ}-{platform.system().lower()}"
    missing_maps = [m for m in plan["maps"] if not (REPO_ROOT / m).is_file()]
    if missing_maps:
        raise EvalRefused(f"map not found: {', '.join(missing_maps)}")
    episodes = plan_episodes(plan["seeds"], plan["maps"], plan["policies"])
    if not repeat:
        refuse_repeated_test_seeds(runs_dir, episodes, ignore=resume)
    if not resume:
        eval_dir.mkdir(parents=True)  # FileExistsError if it is there: an evaluation is never overwritten
        (eval_dir / "plan.json").write_text(json.dumps({**plan, "config_sha256": frozen}, indent=2) + "\n")

    existing = load_episodes(eval_dir)
    done = {_key(e["result"]) for e in existing if e["result"]["outcome"] in OUTCOMES}
    spent = math.fsum(e["result"].get("spend_usd", 0.0) for e in existing)
    stopped, failed_in_a_row = None, 0
    for number, (seed, map_path, policy) in enumerate(episodes, start=1):
        if (policy, map_path, seed) in done:
            continue
        if spent >= plan["budget_usd"]:
            stopped = f"budget of the evaluation spent: ${spent:.6f} of ${plan['budget_usd']:.6f}"
            break
        try:
            result = await run_episode(policy, seed, map_path, plan["runner"], plan["max_seconds"], runs_dir=eval_dir,
                                       ledger_dir=runs_dir, budget_usd=min(plan["per_episode_usd"], plan["budget_usd"] - spent))
        except Exception as error:  # no key, no budget, a bad ledger: nothing more can be played, but what was played is reported
            stopped = f"{type(error).__name__}: {error}"
            break
        spent += result.get("spend_usd", 0.0)
        say(_progress(number, len(episodes), seed, map_path, policy, result))
        failed_in_a_row = failed_in_a_row + 1 if result["outcome"] == "error" else 0
        if failed_in_a_row >= FAILED_IN_A_ROW_LIMIT:
            stopped = f"{FAILED_IN_A_ROW_LIMIT} episodes failed in a row (the last: {result.get('error', 'no message')})"
            break

    loaded = load_episodes(eval_dir)
    finished = {_key(e["result"]) for e in loaded if e["result"]["outcome"] in OUTCOMES}
    planned = {(policy, map_path, seed) for seed, map_path, policy in episodes}
    summary = {
        "kind": "eval", "run_id": eval_dir.name, "config_sha256": config_sha256(), "frozen_sha256": frozen, "plan": plan,
        "episodes_planned": len(planned), "episodes_done": len(finished & planned),
        "errors": sum(e["result"]["outcome"] not in OUTCOMES for e in loaded),
        "spend_usd": math.fsum(e["result"].get("spend_usd", 0.0) for e in loaded),
        "complete": planned <= finished, "stopped": stopped,
    }
    (eval_dir / "report.md").write_text(build_report(loaded, plan, eval_dir.name, frozen, config_sha256(), stopped) + "\n")
    (eval_dir / "result.json").write_text(json.dumps(summary, indent=2) + "\n")
    return summary
