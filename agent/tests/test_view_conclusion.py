"""Spec 003, V4 (AC5): every number on the conclusion card is the one the data gives.

`card_problems` recomputes each fact of the card from the runs of the evaluation (R17) and of the tuning (R15) and checks
that each line says what its facts say. The tests run it on the card itself and, so that it is known to be able to fail, on
copies of the card that are wrong in one way each. The words of the card are the owner's (tasks.md, V4); when they change,
this test is changed with them, and still has to find every number in the data.
"""

import copy
import json
import math
import re
import statistics

import pytest

from kube_agent import view
from kube_agent.config import RUNS_DIR
from kube_agent.evaluation import FROZEN_PATH
from kube_agent.policies import scripted_tactic

CARD = json.loads(view.CONCLUSION_PATH.read_text())
EVALUATION = RUNS_DIR / CARD["facts"]["evaluation"]
FIRST_WORDING = "2d735966627d"  # config_sha256 of the runs before the question was rewritten (T7, T8 baseline)
TUNING_MAP = "maps/bonus/subject_map.cub"
TUNING_FROM = "20261008"  # the T8 baseline began that day; the one T7 episode with the same wording was played on the 6th


def _runs(folder, policy):
    for directory in sorted(folder.glob("2*")):
        result = json.loads((directory / "result.json").read_text())
        if result["policy"] == policy:
            rows = [json.loads(line) for line in (directory / "decisions.jsonl").read_text().splitlines()]
            yield result, rows


def _answered(rows):
    return [row for row in rows if row.get("source") == "jev" and not row.get("error")]


def _sign_test_p(faster, slower):
    n = faster + slower
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(max(faster, slower), n + 1)) / 2**n) if n else 1.0


def computed_facts() -> dict:
    """The facts of the card, from the raw files."""
    jev, rules = list(_runs(EVALUATION, "jev")), list(_runs(EVALUATION, "scripted"))
    everything = [json.loads((d / "result.json").read_text()) for d in sorted(EVALUATION.glob("2*"))]
    maps = sorted({result["map"] for result in everything})

    agreement, p_values = [], []
    for map_path in maps:
        rows = [row for result, group in jev if result["map"] == map_path for row in _answered(group)]
        agreement.append(100 * sum(row["tactic"] == scripted_tactic(row["state"]) for row in rows) / len(rows))
        by_seed = {policy: {r["seed"]: r["survival_seconds"] for r, _ in runs if r["map"] == map_path and r["outcome"] == "win"}
                   for policy, runs in (("jev", jev), ("rules", rules))}
        diffs = [by_seed["jev"][s] - by_seed["rules"][s] for s in by_seed["jev"].keys() & by_seed["rules"].keys()]
        p_values.append(_sign_test_p(sum(d < 0 for d in diffs), sum(d > 0 for d in diffs)))

    latencies = sorted(row["latency_ms"] for _, group in jev for row in _answered(group))
    tuning = [result for result, _ in _runs(RUNS_DIR, "jev")
              if result["map"] == TUNING_MAP and result["seed"] <= 20 and result["runner"] == "docker" and result["run_id"][:8] >= TUNING_FROM]
    first = [r for r in tuning if r["config_sha256"].startswith(FIRST_WORDING)]
    final = [r for r in tuning if r["config_sha256"] == json.loads(FROZEN_PATH.read_text())["config_sha256"]]
    stamp = CARD["facts"]["evaluation"].split("-")[1][:8]
    return {
        "evaluation": EVALUATION.name,
        "games": len(everything),
        "seeds": len({result["seed"] for result in everything}),
        "maps": len(maps),
        "date": f"{stamp[:4]}-{stamp[4:6]}-{stamp[6:]}",
        "model": json.loads(FROZEN_PATH.read_text())["model"],
        "jev_wins": sum(result["outcome"] == "win" for result, _ in jev),
        "jev_games": len(jev),
        "rules_wins": sum(result["outcome"] == "win" for result, _ in rules),
        "rules_games": len(rules),
        "agreement_percent": [round(min(agreement)), round(max(agreement))],
        "time_to_win_sign_test_p_above": math.floor(min(p_values) * 10) / 10,
        "cost_per_game_usd": round(statistics.fmean(result["spend_usd"] for result, _ in jev), 3),
        "latency_p50_s": round(latencies[math.ceil(0.5 * len(latencies)) - 1] / 1000, 1),
        "first_wording": {"games_with_damage": sum(r["damage_taken"] > 0 for r in first), "games": len(first)},
        "final_wording": {"games_with_damage": sum(r["damage_taken"] > 0 for r in final), "games": len(final)},
    }


COMPUTED = computed_facts()


def card_problems(card: dict) -> list[str]:
    """What the card says that the data does not, and what its lines say that its facts do not."""
    found = [f"fact {key}: the card says {card['facts'].get(key)!r}, the data give {value!r}"
             for key, value in COMPUTED.items() if card["facts"].get(key) != value]
    f = card["facts"]
    low, high = f["agreement_percent"]
    expected = [
        f"Jev won {f['jev_wins']} of {f['jev_games']} games.",
        f"Four hand-written rules won {f['rules_wins']} of {f['rules_games']} too.",
        f"Jev matched the rules in {low} to {high}% of its decisions.",
        "No difference in how fast they won.",
        f"About ${f['cost_per_game_usd']} a game, and an answer in {f['latency_p50_s']} s.",
        "",  # a gap: what follows is the tuning, on development seeds
        "Rewording the four options changed its play:",
        f"games with damage went from {f['first_wording']['games_with_damage']} of {f['first_wording']['games']} "
        f"to {f['final_wording']['games_with_damage']} of {f['final_wording']['games']}.",
    ]
    found += [f"line {i}: the card says {line!r}, its facts say {want!r}" for i, (line, want) in enumerate(zip(card["lines"], expected), 1) if line != want]
    if len(card["lines"]) != len(expected):
        found.append(f"the card has {len(card['lines'])} lines, the test knows {len(expected)}")
    source = (f"Held-out seeds: {f['games']} games, {f['seeds']} seeds, {f['maps']} maps, a Mac, {f['date']}.\n"
              f"The options result is from development seeds. {f['model']}. R17, R15.")
    if card["source"] != source:
        found.append(f"the source says {card['source']!r}, the facts say {source!r}")
    numbers_in_lines = sorted(re.findall(r"\d+(?:\.\d+)?", " ".join(card["lines"])))
    numbers_in_facts = sorted(re.findall(r"\d+(?:\.\d+)?", " ".join(expected)))
    if numbers_in_lines != numbers_in_facts:
        found.append(f"the numbers in the lines {numbers_in_lines} are not those of the facts {numbers_in_facts}")
    return found


# --- the card that is in the repository ----------------------------------------------------------------------------------


def test_the_card_says_what_the_data_say():
    assert card_problems(CARD) == []


def test_the_evaluation_is_the_one_of_r17():
    assert (COMPUTED["games"], COMPUTED["seeds"], COMPUTED["maps"]) == (120, 20, 2)
    assert (COMPUTED["jev_games"], COMPUTED["rules_games"]) == (40, 40)


def test_the_tuning_runs_are_the_ones_of_r15():
    assert COMPUTED["first_wording"] == {"games_with_damage": 6, "games": 20}
    assert COMPUTED["final_wording"] == {"games_with_damage": 1, "games": 40}


# --- the check can fail: one wrong thing at a time -------------------------------------------------------------------------


def changed(path, value):
    card = copy.deepcopy(CARD)
    target = card
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    return card


BREAKS = [
    ("Jev wins one fewer", changed(["facts", "jev_wins"], 39), "fact jev_wins"),
    ("the rules played 39 games", changed(["facts", "rules_games"], 39), "fact rules_games"),
    ("agreement said 95 to 98", changed(["facts", "agreement_percent"], [95, 98]), "fact agreement_percent"),
    ("the cost said a cent", changed(["facts", "cost_per_game_usd"], 0.01), "fact cost_per_game_usd"),
    ("the latency said a second", changed(["facts", "latency_p50_s"], 1.0), "fact latency_p50_s"),
    ("the sign test said 0.9", changed(["facts", "time_to_win_sign_test_p_above"], 0.9), "fact time_to_win_sign_test_p_above"),
    ("damage before said 7 of 20", changed(["facts", "first_wording"], {"games_with_damage": 7, "games": 20}), "fact first_wording"),
    ("damage after said none", changed(["facts", "final_wording"], {"games_with_damage": 0, "games": 40}), "fact final_wording"),
    ("another model", changed(["facts", "model"], "typesafe/jev-latest"), "fact model"),
    ("a line with another number", changed(["lines", 0], "Jev won 41 of 40 games."), "line 1"),
    ("a line that claims more", changed(["lines", 3], "Jev was faster."), "line 4"),
    ("the gap is gone", changed(["lines"], [line for line in CARD["lines"] if line]), "the card has 7 lines"),
    ("a number only in the lines", changed(["lines", 4], "About $0.001 a game, and an answer in 0.3 s, 99% of the time."), "line 5"),
    ("the source says all seeds are held out", changed(["source"], "120 games, 20 held-out seeds, 2 maps, a Mac, 2026-10-10.\ntypesafe/jev-1.13. R17, R15."), "the source says"),
    ("a line is missing", changed(["lines"], CARD["lines"][:-1]), "the card has 7 lines"),
]


@pytest.mark.parametrize("name, card, expected", BREAKS, ids=[item[0] for item in BREAKS])
def test_the_check_catches_it(name, card, expected):
    found = card_problems(card)

    assert any(expected in problem for problem in found), found
