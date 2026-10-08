"""The option-order check of T8 (tasks.md): does Jev's choice depend on the order the options are listed in?

R5 says jev-1.13 leans toward the first option of a Choice, and ENGAGE is listed first. Each logged state
is asked three times: in the current order, in the opposite order and in the current order again. The
third answer is the control. The same request does not always get the same answer (R12), so part of any
difference between the two orders is the model's own noise and not the order.

The cost is in the ledger like any other paid call, and the probe stops by itself like the latency one
(see probes.run_probe).
"""

import json
import random
from collections.abc import Mapping
from pathlib import Path

from kube_agent.config import RUNS_DIR
from kube_agent.probes import run_probe, summarize_latency
from kube_agent.stats import wilson_interval

DEV_SEEDS = range(1, 21)  # the development seeds. 101-120 are the test seeds and are never touched here
NEUTRAL_LIMIT = 0.10  # ASSUMPTION of tasks.md: the order is not neutral if MORE than this share of choices differ
VARIANTS = ("current", "reversed", "current_again")


def load_dev_states(runs_dir: Path, n: int, sample_seed: int = 0) -> list[dict]:
    """n distinct states that Jev was asked on development seeds, drawn at random but the same way every time.

    Each item is {"run_id", "row", "state"}: the run, the row of its decisions.jsonl and the state sent. Only
    the answers of the Jev policy count (not the scripted fallback), only from episodes on a development
    seed, and a state logged twice is one state.
    """
    candidates, seen = [], set()
    for folder in sorted(runs_dir.iterdir()):
        result_path = folder / "result.json"
        if not result_path.is_file():
            continue  # a probe that wrote nothing yet, or a file
        result = json.loads(result_path.read_text())
        if result.get("policy") != "jev" or result.get("seed") not in DEV_SEEDS:
            continue
        for index, line in enumerate((folder / "decisions.jsonl").read_text().splitlines()):
            row = json.loads(line)
            if row.get("source") != "jev" or "state" not in row:
                continue
            key = json.dumps(row["state"], sort_keys=True)
            if key in seen:
                continue
            seen.add(key)
            candidates.append({"run_id": folder.name, "row": index, "state": row["state"]})
    if len(candidates) < n:
        raise ValueError(f"only {len(candidates)} distinct states were logged on development seeds and {n} were asked")
    return random.Random(sample_seed).sample(candidates, n)


def load_states_of(runs_dir: Path, folder: str, n: int) -> list[dict]:
    """The first n states that an earlier order-check asked, in the same order, so that another wording of the
    question is compared on exactly the same inputs."""
    path = runs_dir / folder
    result = json.loads((path / "result.json").read_text())
    if result.get("kind") != "order-check":
        raise ValueError(f"{folder} is not an order-check folder (its kind is {result.get('kind')!r})")
    asked = {}  # each state was asked three times and the file is in the order of the calls: one entry per state
    for line in (path / "decisions.jsonl").read_text().splitlines():
        row = json.loads(line)
        asked[row["state_index"]] = {"run_id": row["source_run"], "row": row["source_row"], "state": row["state"]}
    if len(asked) < n:
        raise ValueError(f"{folder} holds only {len(asked)} states and {n} were asked")
    return list(asked.values())[:n]


def reversed_options(question: Mapping) -> dict:
    """The same question with its options listed in the opposite order. Every text stays as it is."""
    flipped = dict(question)
    flipped["criteria"] = dict(reversed(list(question["criteria"].items())))
    return flipped


def order_requests(states: list[dict], question: Mapping) -> list[dict]:
    """Three requests per state: the current order, the opposite order and the current order again."""
    flipped = reversed_options(question)
    requests = []
    for index, item in enumerate(states):
        for variant, asked in zip(VARIANTS, (question, flipped, question)):
            requests.append({
                "state_index": index, "variant": variant, "source_run": item["run_id"], "source_row": item["row"],
                "order": list(asked["criteria"]),
                "state": item["state"], "questions": {"tactic": asked},
            })
    return requests


def _answer(row: dict | None, options: list[str]) -> tuple[str, Mapping] | None:
    """The (choice, probabilities) of a row, or None if it has no usable answer."""
    if row is None or row["error"] is not None:
        return None
    answer = (row["answers"] or {}).get("tactic")
    if not isinstance(answer, dict) or answer.get("choice") not in options:
        return None
    return answer["choice"], answer.get("probabilities") or {}


def _share(count: int, n: int) -> dict:
    return {"count": count, "rate": count / n, "wilson95": list(wilson_interval(count, n))}


def _compare_orders(rows: list[dict], options: list[str]) -> dict | None:
    by_state: dict[int, dict[str, dict]] = {}
    for row in rows:
        by_state.setdefault(row["state_index"], {})[row["variant"]] = row
    complete = []  # for each state with all three answers: {variant: (choice, probabilities)}
    for variants in by_state.values():
        answers = {variant: _answer(variants.get(variant), options) for variant in VARIANTS}
        if all(answers.values()):
            complete.append(answers)
    if not complete:
        return None

    n = len(complete)
    first, last = options[0], options[-1]
    differs_between = sum(a["current"][0] != a["reversed"][0] for a in complete)
    differs_same = sum(a["current"][0] != a["current_again"][0] for a in complete)

    def chosen(variant: str, option: str) -> float:
        return sum(a[variant][0] == option for a in complete) / n

    def mean_probability(variant: str) -> dict:
        return {option: sum(a[variant][1].get(option, 0.0) for a in complete) / n for option in options}

    return {
        "options": list(options),
        "states": n,
        "incomplete_states": len(by_state) - n,
        "differs_between_orders": _share(differs_between, n),
        "differs_same_order": _share(differs_same, n),
        "first_in_current": {"option": first, "chosen_listed_first": chosen("current", first), "chosen_listed_last": chosen("reversed", first)},
        "last_in_current": {"option": last, "chosen_listed_first": chosen("reversed", last), "chosen_listed_last": chosen("current", last)},
        "mean_probability": {"current": mean_probability("current"), "reversed": mean_probability("reversed")},
        "limit": NEUTRAL_LIMIT,
        "not_neutral": differs_between / n > NEUTRAL_LIMIT,
    }


def summarize_order_check(rows: list[dict], requested: int, stopped: str | None, options: list[str]) -> dict:
    """The numbers every probe reports, plus the comparison of the orders over the states answered all three ways."""
    return {**summarize_latency(rows, requested, stopped), "order": _compare_orders(rows, options)}


async def run_order_check(client, states: list[dict], question: Mapping, runs_dir: Path = RUNS_DIR, utc_now=None) -> dict:
    """Ask every state three times and write agent/runs/order-check-<UTC date-time>-<machine>/."""
    options = list(question["criteria"])
    return await run_probe(
        client, "order-check", order_requests(states, question),
        lambda rows, requested, stopped: summarize_order_check(rows, requested, stopped, options),
        runs_dir=runs_dir, utc_now=utc_now,
    )


def describe_order_check(result: dict) -> str:
    """The line `kube-agent order-check` ends with."""
    head = f"order-check: {result['calls_made']} calls ({result['ok']} ok, {result['errors']} errors)"
    tail = f"${result['spend_usd']:.6f} in all | [{result['run_id']}]"
    order = result["order"]
    if order is None:
        return f"{head} | no state was answered in all three ways | {tail}"
    states, between, same = order["states"], order["differs_between_orders"], order["differs_same_order"]
    low, high = between["wilson95"]
    first, last = order["first_in_current"], order["last_in_current"]
    verdict = (
        f"the order is NOT neutral (more than {order['limit']:.0%} differ)" if order["not_neutral"]
        else f"the order looks neutral ({order['limit']:.0%} or fewer differ)"
    )
    return (
        f"{head} over {states} states | the choice differs between the two orders in {between['count']} of {states} "
        f"({between['rate']:.0%}, 95% interval {low * 100:.0f}-{high:.0%}) | asking the same order twice it differs in "
        f"{same['count']} of {states} | {first['option']} is chosen {first['chosen_listed_first']:.0%} of the time listed "
        f"first and {first['chosen_listed_last']:.0%} listed last; {last['option']} {last['chosen_listed_first']:.0%} "
        f"listed first and {last['chosen_listed_last']:.0%} listed last | {verdict} | {tail}"
    )
