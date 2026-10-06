import json

import pytest

from kube_agent.config import TOTAL_BUDGET_USD
from kube_agent.ledger import BudgetExhausted, Ledger, LedgerError, read_ledger, require_budget


def write_rows(folder, rows, name="decisions.jsonl"):
    folder.mkdir(parents=True, exist_ok=True)
    (folder / name).write_text("".join(json.dumps(row) + "\n" for row in rows))


def test_the_total_budget_is_one_dollar():
    assert TOTAL_BUDGET_USD == 1.00


def test_a_missing_or_empty_runs_folder_has_spent_nothing(tmp_path):
    assert read_ledger(tmp_path / "does_not_exist") == Ledger(spent=0.0, paid_calls=0, files=0)
    assert read_ledger(tmp_path) == Ledger(spent=0.0, paid_calls=0, files=0)


def test_it_adds_up_the_cost_of_every_decisions_file_at_any_depth(tmp_path):
    write_rows(tmp_path / "20261006T000000Z-jev-s1-darwin", [{"t": 0.0, "cost": 0.000054}, {"t": 0.5, "cost": 0.000054}])
    write_rows(tmp_path / "eval-20261007T000000Z-darwin" / "ep1", [{"t": 0.0, "cost": 0.0001}])
    write_rows(tmp_path / "latency-20261006T000000Z-darwin", [{"cost": 0.000042}, {"cost": 0.000042}])

    ledger = read_ledger(tmp_path)

    assert ledger.spent == pytest.approx(0.000054 * 2 + 0.0001 + 0.000042 * 2)
    assert (ledger.paid_calls, ledger.files) == (5, 3)


def test_rows_without_a_cost_cost_nothing_and_are_not_paid_calls(tmp_path):
    write_rows(tmp_path / "scripted", [{"t": 0.0, "tactic": "ENGAGE", "applied": True}, {"t": 0.5, "cost": None}, {"cost": 0.0}])

    assert read_ledger(tmp_path) == Ledger(spent=0.0, paid_calls=0, files=1)


def test_only_decisions_files_count_so_a_cost_is_never_counted_twice(tmp_path):
    # result.json carries spend_usd (the sum of the same rows) and episode.jsonl is a path: neither is the ledger.
    write_rows(tmp_path / "run", [{"cost": 0.25}])
    write_rows(tmp_path / "run", [{"cost": 0.25}], name="episode.jsonl")
    (tmp_path / "run" / "result.json").write_text(json.dumps({"spend_usd": 0.25, "cost": 0.25}))

    assert read_ledger(tmp_path).spent == 0.25


def test_ten_dimes_make_exactly_one_dollar(tmp_path):
    # 0.1 added ten times with plain + gives 0.9999999999999999; the ledger must not.
    write_rows(tmp_path / "run", [{"cost": 0.1}] * 10)

    assert read_ledger(tmp_path).spent == 1.0


@pytest.mark.parametrize("line, problem", [
    ("not json at all", "not JSON"),
    ("[1, 2]", "not a JSON object"),
    ('{"cost": "0.1"}', "cost"),
    ('{"cost": true}', "cost"),
    ('{"cost": -0.5}', "cost"),
    ('{"cost": NaN}', "cost"),
])
def test_a_bad_row_stops_the_ledger_and_names_the_file_and_line(tmp_path, line, problem):
    # Guessing a bad row as zero would let the budget be exceeded without a sound.
    folder = tmp_path / "run"
    folder.mkdir()
    (folder / "decisions.jsonl").write_text('{"cost": 0.1}\n' + line + "\n")

    with pytest.raises(LedgerError) as error:
        read_ledger(tmp_path)

    assert "decisions.jsonl:2" in str(error.value)
    assert problem in str(error.value)


def test_blank_lines_are_ignored(tmp_path):
    folder = tmp_path / "run"
    folder.mkdir()
    (folder / "decisions.jsonl").write_text('{"cost": 0.1}\n\n   \n{"cost": 0.2}\n')

    assert read_ledger(tmp_path).spent == pytest.approx(0.3)


def test_what_is_left_never_goes_below_zero():
    assert Ledger(spent=0.25, paid_calls=1, files=1).remaining == pytest.approx(0.75)
    assert Ledger(spent=1.5, paid_calls=1, files=1).remaining == 0.0


def test_the_budget_is_required_while_something_is_left(tmp_path):
    write_rows(tmp_path / "run", [{"cost": 0.999999}])

    ledger = require_budget(tmp_path)

    assert ledger.remaining == pytest.approx(0.000001)


@pytest.mark.parametrize("rows", [[{"cost": 1.0}], [{"cost": 0.1}] * 10, [{"cost": 0.6}, {"cost": 0.7}]])
def test_a_ledger_at_or_over_one_dollar_refuses(tmp_path, rows):
    write_rows(tmp_path / "run", rows)

    with pytest.raises(BudgetExhausted, match=r"\$1\.00 total budget is spent"):
        require_budget(tmp_path)


def test_the_message_names_how_much_is_in_the_ledger(tmp_path):
    write_rows(tmp_path / "run", [{"cost": 1.25}])

    with pytest.raises(BudgetExhausted) as error:
        require_budget(tmp_path)

    assert "$1.250000" in str(error.value)
