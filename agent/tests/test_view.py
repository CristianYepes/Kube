"""Spec 003, V2: the events `kube-agent view` makes from a run folder, live and in replay.

The page draws only what these events say, so this is where what it can show is decided: the rules' choice, the four
probabilities, at most three facts, and no milliseconds.
"""

import json
import threading
import time

import pytest

from kube_agent import view
from kube_agent.config import RUNS_DIR
from kube_agent.controller import TACTICS
from kube_agent.policies import scripted_tactic

EVAL = RUNS_DIR / "eval-20261010T122708Z-darwin"
JEV_FOLDERS = sorted(EVAL.glob("*-jev-*"))
SCRIPTED_FOLDER = sorted(EVAL.glob("*-scripted-*"))[0]
ERROR_FOLDER = RUNS_DIR / "20261008T090926Z-jev-s12-darwin"  # a call that timed out in T8 (research of spec 002, R15)
LATE_FOLDER = next(folder for folder in JEV_FOLDERS if '"episode_ended"' in (folder / "decisions.jsonl").read_text())
JEV_ROWS = [json.loads(line) for folder in JEV_FOLDERS for line in (folder / "decisions.jsonl").read_text().splitlines()]
VOCABULARY = {
    "grunt", "runner", "boss", "touching", "close", "medium", "far", "ahead", "behind", "left", "right", "ahead-left",
    "ahead-right", "behind-left", "behind-right", "no", "zombie", "left", "being", "hit", "cornered", "health", "low",
    "in", "view",
}


def a_state(nearest=("runner", "close", "left"), in_view=1, remaining=3, being_hit=False, cornered=False, health="high"):
    kind, distance, direction = nearest if nearest else (None, None, None)
    return {
        "player": {"health": health, "weapon": "ready", "being_hit": being_hit},
        "threats": {
            "remaining": remaining, "in_view": in_view, "close_count": 1,
            "nearest": {"kind": kind, "distance": distance, "direction": direction, "wounded": False} if nearest else None,
        },
        "space": {"open_directions": ["ahead"], "cornered": cornered},
        "progress": {"wave": "1 of 3", "boss_present": False},
        "current_tactic": "ENGAGE",
    }


def a_run(tmp_path, name="20991231T235959Z-jev-s3-darwin"):
    folder = tmp_path / name
    folder.mkdir()
    return folder


def append(path, row):
    with path.open("a") as file:
        file.write(json.dumps(row) + "\n")


# --- the data ----------------------------------------------------------------------------------------------------------


def test_the_t9_runs_are_there():
    assert len(JEV_FOLDERS) == 40 and len(JEV_ROWS) == 1302
    assert ERROR_FOLDER.is_dir()


# --- what Jev read, in at most three facts -------------------------------------------------------------------------------


def test_every_t9_state_gives_one_to_three_short_facts():
    for row in JEV_ROWS:
        facts = view.describe_state(row["state"])
        assert 1 <= len(facts) <= 3, facts
        assert all(0 < len(fact) <= 32 for fact in facts), facts


def test_every_word_of_the_facts_comes_from_a_fixed_vocabulary():
    words = {word.strip(",") for row in JEV_ROWS for fact in view.describe_state(row["state"]) for word in fact.split()}
    assert {word for word in words if not word.isdigit()} <= VOCABULARY


def test_the_first_fact_is_the_nearest_threat():
    assert view.describe_state(a_state())[0] == "runner, close, left"


def test_a_calm_state_ends_with_the_count():
    assert view.describe_state(a_state(nearest=("grunt", "far", "ahead"))) == ["grunt, far, ahead", "1 in view, 3 left"]


def test_flags_come_before_the_count_and_the_list_stops_at_three():
    state = a_state(being_hit=True, cornered=True, health="low")
    assert view.describe_state(state) == ["runner, close, left", "being hit", "cornered"]


def test_health_is_said_only_when_it_is_not_high():
    assert view.describe_state(a_state(health="medium")) == ["runner, close, left", "health medium", "1 in view, 3 left"]


def test_a_state_with_no_zombie_says_so():
    assert view.describe_state(a_state(nearest=None, in_view=0, remaining=0)) == ["no zombie left"]


# --- decision events -------------------------------------------------------------------------------------------------------


def test_a_jev_decision_carries_the_rules_choice_and_the_four_probabilities():
    row = next(row for row in JEV_ROWS if row["applied"])
    event = view.decision_event(row)

    assert event["kind"] == "decision" and event["source"] == "jev" and event["tactic"] == row["tactic"]
    assert event["rules"] == scripted_tactic(row["state"])
    assert set(event["probabilities"]) == set(TACTICS)
    assert sum(event["probabilities"].values()) == pytest.approx(1.0, abs=0.01)
    assert event["read"] == view.describe_state(row["state"])


def test_the_rules_choice_is_the_real_rules_on_every_t9_decision():
    assert all(view.decision_event(row)["rules"] == scripted_tactic(row["state"]) for row in JEV_ROWS)


def test_milliseconds_cost_and_the_raw_state_are_not_sent_to_the_page():
    event = view.decision_event(JEV_ROWS[0])
    assert not {"latency_ms", "cost", "input_tokens", "model", "state", "answers", "error"} & set(event)


def test_a_decision_that_failed_has_no_tactic_and_is_not_applied():
    rows = [json.loads(line) for line in (ERROR_FOLDER / "decisions.jsonl").read_text().splitlines()]
    event = view.decision_event(next(row for row in rows if row.get("error")))
    assert event["tactic"] is None and event["applied"] is False and event["probabilities"] is None


def test_a_scripted_decision_has_no_probabilities():
    row = json.loads((SCRIPTED_FOLDER / "decisions.jsonl").read_text().splitlines()[0])
    event = view.decision_event(row)
    assert event["probabilities"] is None and event["source"] == "scripted" and event["answered_at"] == row["t"]


def test_the_log_numbers_events_from_zero_and_gives_those_after_a_number():
    log = view.EventLog()
    assert log.after(-1) == []
    assert [log.append({"kind": "row", "t": i}) for i in range(3)] == [0, 1, 2]
    assert [event["n"] for event in log.after(-1)] == [0, 1, 2]
    assert [event["n"] for event in log.after(0)] == [1, 2]
    assert log.after(2) == [] and log.after(99) == []
    assert [event["n"] for event in log.after(-7)] == [0, 1, 2]


def test_an_answer_that_came_after_the_end_has_no_answered_at():
    rows = [json.loads(line) for line in (LATE_FOLDER / "decisions.jsonl").read_text().splitlines()]
    late = [row for row in rows if row["reason"] == "episode_ended"]
    assert late and all(view.decision_event(row)["answered_at"] is None for row in late)


# --- reading a folder that is still being written --------------------------------------------------------------------------


def test_a_folder_with_no_files_yet_gives_nothing(tmp_path):
    assert view.RunReader(a_run(tmp_path)).read_new() == []


def test_a_half_written_line_waits_for_the_next_read(tmp_path):
    folder = a_run(tmp_path)
    reader = view.RunReader(folder)
    (folder / "episode.jsonl").write_text(json.dumps({"t": 0.0, "tactic": "ENGAGE"}) + "\n" + '{"t": 0.5, "tac')

    assert [event["t"] for event in reader.read_new()] == [0.0]
    with (folder / "episode.jsonl").open("a") as file:
        file.write('tic": "KITE"}\n')
    assert [(event["t"], event["tactic"]) for event in reader.read_new()] == [(0.5, "KITE")]
    assert reader.read_new() == []


def test_result_json_gives_one_end_event(tmp_path):
    folder = a_run(tmp_path)
    reader = view.RunReader(folder)
    (folder / "result.json").write_text(json.dumps({"outcome": "win", "survival_seconds": 13.6, "damage_taken": 0}))

    assert reader.read_new() == [{"kind": "end", "outcome": "win", "survival_seconds": 13.6, "damage_taken": 0}]
    assert reader.ended and reader.read_new() == []


def test_a_result_json_being_written_is_read_on_a_later_poll(tmp_path):
    folder = a_run(tmp_path)
    reader = view.RunReader(folder)
    (folder / "result.json").write_text('{"outcome": "win", "surv')

    assert reader.read_new() == [] and not reader.ended


def test_a_line_that_is_not_json_is_reported_and_the_next_lines_are_still_served(tmp_path):
    folder = a_run(tmp_path)
    reader = view.RunReader(folder)
    (folder / "episode.jsonl").write_text(
        '{"t": 0.0, "tactic": "ENGAGE"}\nthis is not json\n{"t": 0.5, "tactic": "KITE"}\n{"tactic": "KITE"}\n')

    assert [event["t"] for event in reader.read_new()] == [0.0, 0.5]
    assert len(reader.problems) == 2
    assert "episode.jsonl line 2" in reader.problems[0] and "episode.jsonl line 4" in reader.problems[1]


def test_a_result_json_that_never_becomes_readable_is_reported_once(tmp_path):
    folder = a_run(tmp_path)
    reader = view.RunReader(folder)
    (folder / "result.json").write_text("not json at all")

    for _ in range(view.UNREADABLE_RESULT_POLLS * 2):
        assert reader.read_new() == []
    assert len(reader.problems) == 1 and "result.json" in reader.problems[0]


def test_a_row_written_just_before_result_json_is_never_lost(tmp_path, monkeypatch):
    """The agent finishes in the middle of a poll: its last row and result.json appear after we looked at the rows."""
    folder = a_run(tmp_path)
    reader = view.RunReader(folder)
    original, fired = reader._read_lines, []

    def read_lines(name, make):
        events = original(name, make)
        if not fired:
            fired.append(name)
            append(folder / "episode.jsonl", {"t": 9.0, "tactic": "KITE"})
            (folder / "result.json").write_text(json.dumps({"outcome": "win", "survival_seconds": 9.0, "damage_taken": 0}))
        return events

    monkeypatch.setattr(reader, "_read_lines", read_lines)
    seen = reader.read_new() + reader.read_new() + reader.read_new()

    assert [(event["kind"], event.get("t")) for event in seen] == [("row", 9.0), ("end", None)]


# --- follow: the live mode ----------------------------------------------------------------------------------------------


def run_follow(tmp_path, since):
    log, stop = view.EventLog(), threading.Event()
    thread = threading.Thread(target=view.follow, args=(log, stop), kwargs={"runs_dir": tmp_path, "since": since}, daemon=True)
    thread.start()
    return log, stop, thread


def test_follow_serves_each_line_within_150_ms_of_its_writing(tmp_path):
    """AC1: the page asks every 50 ms, like this test does."""
    log, stop, thread = run_follow(tmp_path, since="20990101T000000Z")
    written, seen = {}, {}

    def page():
        after = -1
        while not stop.is_set():
            for event in log.after(after):
                after = event["n"]
                if event["kind"] == "row":
                    seen[event["t"]] = time.monotonic()
            time.sleep(view.PAGE_POLL_SECONDS)

    reader = threading.Thread(target=page, daemon=True)
    reader.start()
    folder = a_run(tmp_path)
    for i in range(10):
        written[i * 0.5] = time.monotonic()
        append(folder / "episode.jsonl", {"t": i * 0.5, "tactic": "ENGAGE"})
        time.sleep(0.1)
    time.sleep(0.3)
    stop.set()
    thread.join(1)

    delays = [seen[t] - written[t] for t in written]
    assert len(delays) == 10 and max(delays) <= 0.15, delays


def test_follow_starts_with_a_run_event_and_ignores_older_folders(tmp_path):
    a_run(tmp_path, "20991231T000000Z-jev-s1-darwin")
    log, stop, thread = run_follow(tmp_path, since="20991231T120000Z")
    time.sleep(0.2)
    assert log.after(-1) == []

    a_run(tmp_path, "20991231T235959Z-jev-s3-darwin")
    time.sleep(0.2)
    stop.set()
    thread.join(1)
    events = log.after(-1)
    assert events[0] == {"n": 0, "kind": "run", "run_id": "20991231T235959Z-jev-s3-darwin", "policy": "jev", "seed": 3,
                         "mode": "live"}


def test_follow_moves_on_to_a_newer_run(tmp_path):
    log, stop, thread = run_follow(tmp_path, since="20990101T000000Z")
    a_run(tmp_path, "20991231T000000Z-scripted-s1-darwin")
    time.sleep(0.2)
    a_run(tmp_path, "20991231T000100Z-jev-s2-darwin")
    time.sleep(0.2)
    stop.set()
    thread.join(1)
    assert [event["run_id"] for event in log.after(-1) if event["kind"] == "run"] == [
        "20991231T000000Z-scripted-s1-darwin", "20991231T000100Z-jev-s2-darwin"]


def test_follow_takes_a_run_created_in_the_same_second_as_the_start(tmp_path):
    a_run(tmp_path, "20991231T000000Z-jev-s1-darwin")
    log, stop, thread = run_follow(tmp_path, since="20991231T000000Z")
    time.sleep(0.2)
    stop.set()
    thread.join(1)
    assert [event["run_id"] for event in log.after(-1) if event["kind"] == "run"] == ["20991231T000000Z-jev-s1-darwin"]


def test_follow_does_not_take_evaluation_or_probe_folders_even_when_they_are_newer(tmp_path):
    a_run(tmp_path, "20991231T000000Z-jev-s1-darwin")
    for name in ("eval-20991231T000100Z-darwin", "order-check-20991231T000100Z-darwin", "20991231T000200Z-notes"):
        a_run(tmp_path, name)
    log, stop, thread = run_follow(tmp_path, since="20990101T000000Z")
    time.sleep(0.2)
    stop.set()
    thread.join(1)
    assert [event["run_id"] for event in log.after(-1) if event["kind"] == "run"] == ["20991231T000000Z-jev-s1-darwin"]


def test_follow_says_once_what_it_could_not_read(tmp_path):
    said, log, stop = [], view.EventLog(), threading.Event()
    (a_run(tmp_path) / "episode.jsonl").write_text("not json\n")
    thread = threading.Thread(target=view.follow, args=(log, stop),
                              kwargs={"runs_dir": tmp_path, "since": "20990101T000000Z", "say": said.append}, daemon=True)
    thread.start()
    time.sleep(0.3)
    stop.set()
    thread.join(1)
    assert len(said) == 1 and "episode.jsonl line 1" in said[0]


# --- replay ---------------------------------------------------------------------------------------------------------------


def test_replay_puts_each_event_at_the_moment_it_happened():
    folder = JEV_FOLDERS[0]
    schedule = view.replay_schedule(folder)
    times = [at for at, _ in schedule]
    result = json.loads((folder / "result.json").read_text())

    assert schedule[0] == (0.0, {"kind": "run", "run_id": folder.name, "policy": "jev", "seed": 101, "mode": "replay"})
    assert times == sorted(times)
    assert schedule[-1][1]["kind"] == "end" and schedule[-1][0] == result["survival_seconds"]
    decisions = [(at, event) for at, event in schedule if event["kind"] == "decision" and event["reason"] != "episode_ended"]
    assert all(at == event["answered_at"] for at, event in decisions)


def test_an_answer_that_came_after_the_end_is_released_just_before_the_end():
    schedule = view.replay_schedule(LATE_FOLDER)
    end_at = json.loads((LATE_FOLDER / "result.json").read_text())["survival_seconds"]
    late = [i for i, (_, event) in enumerate(schedule) if event["kind"] == "decision" and event["reason"] == "episode_ended"]

    assert late and all(schedule[i][0] == end_at for i in late)
    assert late[-1] == len(schedule) - 2 and schedule[-1][1]["kind"] == "end"


def test_replay_until_releases_nothing_after_that_moment():
    log, stop = view.EventLog(), threading.Event()
    now = [0.0]
    view.replay(log, JEV_FOLDERS[0], stop, until=5.0, clock=lambda: now[0], wait=lambda seconds: now.__setitem__(0, now[0] + seconds))

    times = [event.get("answered_at") or event.get("t") or 0.0 for event in log.after(-1)]
    assert times and max(times) <= 5.0
    assert not any(event["kind"] == "end" for event in log.after(-1))


def test_replay_at_real_speed_shows_the_last_decision_on_time(tmp_path):
    """AC6, on a short made-up run: the last decision within 0.2 s of its answered_at."""
    folder = a_run(tmp_path)
    for t in (0.0, 0.5, 1.0, 1.5):
        append(folder / "episode.jsonl", {"t": t, "tactic": "ENGAGE"})
    for t, answered in ((0.0, 0.3), (0.5, 0.9), (1.0, 1.5)):
        append(folder / "decisions.jsonl", {"t": t, "answered_at": answered, "tactic": "KITE", "applied": True, "reason": None,
                                            "source": "jev", "confidence": 1, "answers": None, "state": a_state()})
    log, stop = view.EventLog(), threading.Event()
    start = time.monotonic()
    view.replay(log, folder, stop)

    elapsed = time.monotonic() - start  # replay() returns once it has released the last event
    last = [event for event in log.after(-1) if event["kind"] == "decision"][-1]
    assert last["answered_at"] == 1.5
    assert 1.5 - 0.02 <= elapsed <= 1.5 + 0.2
