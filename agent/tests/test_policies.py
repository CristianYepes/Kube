import json
import re
from pathlib import Path

import pytest
from helpers import ROOM, enemy_ahead, make_obs

from kube_agent.features import HpHistory, semantic_state
from kube_agent.policies import (
    POLICIES,
    DecisionSchedule,
    IdlePolicy,
    ScriptedPolicy,
    make_policy,
    scripted_tactic,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"

CLOSE = enemy_ahead(2.0, 0.0)  # under 2.5 cells, in view
BEHIND_CLOSE = enemy_ahead(-2.0, 0.0)  # under 2.5 cells, behind the player: not in view
FAR_IN_VIEW = enemy_ahead(5.0, 0.0)
FAR_HIDDEN = enemy_ahead(5.0, 0.0, los=0)


def state_for(enemies, hp=100):
    return semantic_state(make_obs(enemies, hp=hp), ROOM, HpHistory(), "ENGAGE")


# --- the four rules -----------------------------------------------------------------------------


@pytest.mark.parametrize("hp, enemies, expected", [
    (20, [CLOSE], "RETREAT"),  # rule 1: health low and something close
    (20, [BEHIND_CLOSE], "RETREAT"),  # close does not need to be in view
    (29, [CLOSE], "RETREAT"),
    (30, [CLOSE], "KITE"),  # 30 is medium, not low
    (100, [CLOSE], "KITE"),  # rule 2: something close
    (100, [BEHIND_CLOSE], "KITE"),  # close beats in view
    (100, [FAR_IN_VIEW], "ENGAGE"),  # rule 3: something in view
    (20, [FAR_IN_VIEW], "ENGAGE"),  # low health with nothing close is not a reason to run
    (100, [FAR_HIDDEN], "SEARCH"),  # rule 4: otherwise
    (100, [], "SEARCH"),
])
def test_scripted_rules(hp, enemies, expected):
    assert scripted_tactic(state_for(enemies, hp)) == expected


# --- when to decide -----------------------------------------------------------------------------


def test_the_first_observation_is_a_decision_point():
    assert DecisionSchedule().due(make_obs(t=0.0)) is True


def test_then_a_decision_is_due_every_half_second_from_the_last_one():
    schedule = DecisionSchedule()
    due = [schedule.due(make_obs(t=t)) for t in (0.0, 0.1, 0.49, 0.5, 0.9, 0.99, 1.0, 1.2)]

    assert due == [True, False, False, True, False, False, True, False]


def test_a_stall_moves_the_next_decision_with_it():
    schedule = DecisionSchedule()
    due = [schedule.due(make_obs(t=t)) for t in (0.0, 0.75, 1.0, 1.25)]  # exact in binary: 1.2 - 0.7 is not 0.5

    assert due == [True, True, False, True]  # 0.75 is late, so the next is at 1.25, not at 1.0


def test_a_decision_made_for_an_event_restarts_the_half_second():
    schedule = DecisionSchedule()
    steps = [(0.0, 1), (0.4, 2), (0.5, 2), (0.75, 2), (0.9, 2)]  # (t, wave): the wave starts at 0.4
    due = [schedule.due(make_obs(t=t, wave=wave)) for t, wave in steps]

    # Decided at 0.0 and at 0.4 (the event). The next is 0.5 s after the event, not at 0.5.
    assert due == [True, True, False, False, True]


def test_a_new_wave_is_due_at_once_and_only_once():
    schedule = DecisionSchedule()
    due = [schedule.due(make_obs(t=t, wave=wave)) for t, wave in [(0.0, 1), (0.1, 1), (0.2, 2), (0.3, 2)]]

    assert due == [True, False, True, False]


def test_a_health_band_drop_is_due_at_once():
    schedule = DecisionSchedule()
    hp_by_time = [(0.0, 100), (0.1, 99), (0.2, 59), (0.3, 58), (0.4, 29)]
    due = [schedule.due(make_obs(t=t, hp=hp)) for t, hp in hp_by_time]

    assert due == [True, False, True, False, True]  # high to medium at 59, medium to low at 29


def test_a_rising_band_is_not_an_event_but_a_later_drop_is():
    schedule = DecisionSchedule()
    due = [schedule.due(make_obs(t=t, hp=hp)) for t, hp in [(0.0, 50), (0.1, 80), (0.2, 50)]]

    assert due == [True, False, True]  # medium to high is nothing; high back to medium is a drop


# --- the scripted policy ------------------------------------------------------------------------


def test_the_initial_tactic_is_engage():
    assert ScriptedPolicy(ROOM).tactic == "ENGAGE"


def test_the_first_observation_makes_a_decision_row():
    policy = ScriptedPolicy(ROOM)

    row = policy.step(make_obs([CLOSE]))

    assert policy.tactic == "KITE"
    assert set(row) == {"t", "state", "tactic", "applied"}
    assert (row["t"], row["tactic"], row["applied"]) == (0.0, "KITE", True)
    assert row["state"]["current_tactic"] == "ENGAGE"  # the state shows the tactic it replaces


def test_between_decisions_the_tactic_is_held_even_when_a_rule_would_change_it():
    policy = ScriptedPolicy(ROOM)
    policy.step(make_obs([FAR_IN_VIEW], t=0.0))

    assert policy.step(make_obs([CLOSE], t=0.1)) is None
    assert policy.tactic == "ENGAGE"
    row = policy.step(make_obs([CLOSE], t=0.5))
    assert (row["t"], row["tactic"]) == (0.5, "KITE")


def test_it_decides_on_jevs_schedule_and_not_on_every_observation():
    policy = ScriptedPolicy(ROOM)

    rows = [policy.step(make_obs([FAR_IN_VIEW], t=index / 100)) for index in range(100)]

    assert [index for index, row in enumerate(rows) if row] == [0, 50]


def test_a_new_wave_makes_it_decide_at_once():
    policy = ScriptedPolicy(ROOM)
    policy.step(make_obs([FAR_IN_VIEW], t=0.0, wave=1))

    row = policy.step(make_obs([CLOSE], t=0.1, wave=2))

    assert row["tactic"] == "KITE"


def test_a_health_band_drop_makes_it_decide_at_once():
    policy = ScriptedPolicy(ROOM)
    policy.step(make_obs([CLOSE], t=0.0, hp=100))

    row = policy.step(make_obs([CLOSE], t=0.1, hp=20))

    assert row["tactic"] == "RETREAT"
    assert row["state"]["player"]["health"] == "low"


def test_being_hit_reads_every_observation_and_not_only_the_decision_ones():
    # hp falls from 100 to 90 at t=0.3, between two decisions. At the event decision of t=1.3 it
    # was already 90 a second earlier, so the player is not being hit. A history fed only at
    # decisions would compare with t=0.0 (hp 100) and say it is.
    policy = ScriptedPolicy(ROOM)
    for t, hp in [(0.0, 100), (0.1, 100), (0.2, 100), (0.3, 90), (0.5, 90), (1.0, 90)]:
        policy.step(make_obs([FAR_IN_VIEW], t=t, hp=hp))

    row = policy.step(make_obs([FAR_IN_VIEW], t=1.3, hp=90, wave=2))

    assert row is not None  # the new wave made it decide
    assert row["state"]["player"]["being_hit"] is False


def floats_in(value):
    if isinstance(value, float):
        yield value
    elif isinstance(value, dict):
        for inner in value.values():
            yield from floats_in(inner)
    elif isinstance(value, list):
        for inner in value:
            yield from floats_in(inner)


@pytest.mark.parametrize("fixture", ["idle_seed7.jsonl", "moves_seed7.jsonl"])
def test_the_decision_rows_over_a_recorded_game_are_small_and_hold_no_float(fixture):
    rows = [json.loads(line) for line in (FIXTURES / fixture).read_text().splitlines()]
    policy = ScriptedPolicy(rows[0]["map"])
    observations = rows[1:]

    decisions = [row for row in map(policy.step, observations) if row]

    seconds = observations[-1]["t"]
    assert seconds / 0.5 <= len(decisions) <= seconds / 0.5 + 6  # every 0.5 s, plus a few events
    for decision in decisions:
        text = json.dumps(decision)
        assert len(text) < 2000
        assert not list(floats_in(decision["state"]))
        assert not re.search(r"\d\.\d", json.dumps(decision["state"]))
        assert decision["tactic"] in ("ENGAGE", "KITE", "RETREAT", "SEARCH")


# --- the idle policy ----------------------------------------------------------------------------


def test_idle_has_no_tactic_and_never_decides():
    rows = [json.loads(line) for line in (FIXTURES / "idle_seed7.jsonl").read_text().splitlines()]
    policy = IdlePolicy()

    results = [policy.step(obs) for obs in rows[1:]]

    assert policy.tactic is None  # no tactic means the episode sends the game no command at all
    assert results == [None] * len(results)


# --- choosing a policy by name ------------------------------------------------------------------


def test_make_policy_builds_the_policy_with_that_name():
    assert POLICIES == ("idle", "scripted")  # "jev" joins when its policy exists
    assert isinstance(make_policy("idle", ROOM), IdlePolicy)
    assert isinstance(make_policy("scripted", ROOM), ScriptedPolicy)


def test_make_policy_rejects_a_name_it_does_not_know():
    with pytest.raises(ValueError, match="policy 'jev'"):
        make_policy("jev", ROOM)
