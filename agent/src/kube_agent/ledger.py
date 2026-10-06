"""The spend ledger: every Jev call's cost is a `cost` in a decisions.jsonl row, and what is spent
is the sum of them all, across every run, probe and evaluation under agent/runs/.

Runs are committed, so the ledger travels with git between the Mac and the owner's Linux
(plan.md, "Budget ledger"). A row that cannot be read stops the ledger: guessing it as zero
would let the budget be exceeded without a sound.
"""

import json
import math
from dataclasses import dataclass
from pathlib import Path

from kube_agent.config import RUNS_DIR, TOTAL_BUDGET_USD


class LedgerError(Exception):
    """A decisions.jsonl row that cannot be read as a cost."""


class BudgetExhausted(Exception):
    """The whole budget is spent: nothing may call Jev any more."""


@dataclass(frozen=True)
class Ledger:
    spent: float
    paid_calls: int  # rows with a cost above zero
    files: int  # decisions.jsonl files read

    @property
    def remaining(self) -> float:
        return max(0.0, TOTAL_BUDGET_USD - self.spent)


def read_ledger(runs_dir: Path = RUNS_DIR) -> Ledger:
    costs: list[float] = []
    files = 0
    for path in sorted(runs_dir.rglob("decisions.jsonl")):
        files += 1
        for number, line in enumerate(path.read_text().splitlines(), start=1):
            if line.strip():
                costs.append(_cost_of_row(path, number, line))
    # fsum: ten rows of 0.1 add up to exactly 1.0, where plain addition gives 0.9999999999999999
    return Ledger(spent=math.fsum(costs), paid_calls=sum(cost > 0 for cost in costs), files=files)


def require_budget(runs_dir: Path = RUNS_DIR) -> Ledger:
    """The ledger, or BudgetExhausted once it has reached the total."""
    ledger = read_ledger(runs_dir)
    if ledger.spent >= TOTAL_BUDGET_USD:
        raise BudgetExhausted(
            f"the ${TOTAL_BUDGET_USD:.2f} total budget is spent (${ledger.spent:.6f} in the ledger "
            f"under {runs_dir}): no more calls to Jev"
        )
    return ledger


def _cost_of_row(path: Path, number: int, line: str) -> float:
    where = f"{path}:{number}"
    try:
        row = json.loads(line)
    except json.JSONDecodeError:
        raise LedgerError(f"{where}: the row is not JSON: {line[:80]!r}") from None
    if not isinstance(row, dict):
        raise LedgerError(f"{where}: the row is not a JSON object: {line[:80]!r}")
    cost = row.get("cost")
    if cost is None:
        return 0.0
    if isinstance(cost, bool) or not isinstance(cost, (int, float)) or not math.isfinite(cost) or cost < 0:
        raise LedgerError(f"{where}: cost must be a finite number of dollars, not negative; got {cost!r}")
    return float(cost)
