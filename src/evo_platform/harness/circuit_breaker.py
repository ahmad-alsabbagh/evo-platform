"""Circuit Breaker - Prevents cascading failures from unhealthy tools.

Implements the classic three-state circuit breaker pattern:
CLOSED (normal) -> OPEN (failing, reject calls) -> HALF_OPEN (testing recovery)
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Callable, Dict, Optional


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpen(Exception):
    """Raised when a call is rejected because the circuit is open."""

    def __init__(self, tool_name: str, retry_after_s: float):
        self.tool_name = tool_name
        self.retry_after_s = retry_after_s
        super().__init__(
            f"Circuit breaker OPEN for tool '{tool_name}'. Retry after {retry_after_s:.1f}s"
        )


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    success_threshold: int = 2
    timeout_s: float = 30.0
    window_s: float = 60.0


class CircuitBreaker:
    """Per-tool circuit breaker with sliding failure window."""

    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failures: list[float] = []
        self._success_count = 0
        self._opened_at: Optional[float] = None
        self._lock = Lock()

    @property
    def state(self) -> CircuitState:
        with self._lock:
            self._maybe_transition_to_half_open()
            return self._state

    def _maybe_transition_to_half_open(self) -> None:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if time.time() - self._opened_at >= self.config.timeout_s:
                self._state = CircuitState.HALF_OPEN
                self._success_count = 0

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def record_success(self) -> None:
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._failures.clear()
                    self._opened_at = None
            elif self._state == CircuitState.CLOSED:
                self._failures.clear()

    def record_failure(self) -> None:
        with self._lock:
            now = time.time()
            if self._state == CircuitState.HALF_OPEN:
                self._open(now)
                return
            self._failures = [t for t in self._failures if now - t <= self.config.window_s]
            self._failures.append(now)
            if len(self._failures) >= self.config.failure_threshold:
                self._open(now)

    def _open(self, now: float) -> None:
        self._state = CircuitState.OPEN
        self._opened_at = now

    def call(self, fn: Callable[[], Any]) -> Any:
        """Execute fn through the circuit breaker."""
        if self.is_open():
            retry_after = max(
                0.0, self.config.timeout_s - (time.time() - (self._opened_at or time.time()))
            )
            raise CircuitBreakerOpen(self.name, retry_after)
        try:
            result = fn()
        except Exception:
            self.record_failure()
            raise
        else:
            self.record_success()
            return result


class CircuitBreakerRegistry:
    """Registry of circuit breakers, one per tool."""

    def __init__(self, default_config: Optional[CircuitBreakerConfig] = None):
        self._breakers: Dict[str, CircuitBreaker] = {}
        self._default_config = default_config or CircuitBreakerConfig()
        self._lock = Lock()

    def get(self, tool_name: str) -> CircuitBreaker:
        with self._lock:
            if tool_name not in self._breakers:
                self._breakers[tool_name] = CircuitBreaker(tool_name, self._default_config)
            return self._breakers[tool_name]

    def status(self) -> Dict[str, str]:
        with self._lock:
            return {name: cb.state.value for name, cb in self._breakers.items()}
