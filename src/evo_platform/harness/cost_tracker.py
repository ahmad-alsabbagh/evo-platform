"""Cost Tracker - Per-tenant, per-agent cost metering with budget enforcement."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Dict, List, Optional


class BudgetExceededError(Exception):
    def __init__(self, scope: str, spent: float, cap: float):
        self.scope = scope
        self.spent = spent
        self.cap = cap
        super().__init__(
            f"Budget exceeded for '{scope}': spent ${spent:.4f} of ${cap:.4f} cap"
        )


@dataclass
class CostEvent:
    scope: str
    agent_id: str
    amount_usd: float
    category: str
    metadata: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class BudgetPolicy:
    scope: str
    cap_usd: float
    period_s: Optional[float] = None


class CostTracker:
    """Thread-safe cost ledger with budget enforcement."""

    def __init__(self):
        self._events: List[CostEvent] = []
        self._budgets: Dict[str, BudgetPolicy] = {}
        self._lock = Lock()

    def set_budget(self, policy: BudgetPolicy) -> None:
        with self._lock:
            self._budgets[policy.scope] = policy

    def _spent_in_window(self, scope: str, period_s: Optional[float]) -> float:
        if period_s is None:
            return sum(e.amount_usd for e in self._events if e.scope == scope)
        cutoff = datetime.now(timezone.utc).timestamp() - period_s
        return sum(
            e.amount_usd
            for e in self._events
            if e.scope == scope and e.timestamp.timestamp() >= cutoff
        )

    def check_budget(self, scope: str, additional_usd: float = 0.0) -> None:
        with self._lock:
            policy = self._budgets.get(scope)
            if policy is None:
                return
            spent = self._spent_in_window(scope, policy.period_s)
            if spent + additional_usd > policy.cap_usd:
                raise BudgetExceededError(scope, spent + additional_usd, policy.cap_usd)

    def record(self, event: CostEvent, enforce: bool = True) -> None:
        if enforce:
            self.check_budget(event.scope, event.amount_usd)
        with self._lock:
            self._events.append(event)

    def total_for_scope(self, scope: str) -> float:
        with self._lock:
            return sum(e.amount_usd for e in self._events if e.scope == scope)

    def total_for_agent(self, agent_id: str) -> float:
        with self._lock:
            return sum(e.amount_usd for e in self._events if e.agent_id == agent_id)

    def breakdown_by_category(self, scope: str) -> Dict[str, float]:
        with self._lock:
            totals: Dict[str, float] = defaultdict(float)
            for e in self._events:
                if e.scope == scope:
                    totals[e.category] += e.amount_usd
            return dict(totals)

    def remaining_budget(self, scope: str) -> Optional[float]:
        with self._lock:
            policy = self._budgets.get(scope)
            if policy is None:
                return None
            spent = self._spent_in_window(scope, policy.period_s)
            return max(0.0, policy.cap_usd - spent)
