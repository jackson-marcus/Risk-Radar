"""Three-state circuit breaker protecting downstream service calls."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    failures: int = 0
    state: str = "closed"

    def allow(self) -> bool:
        return self.state != "open"

    def record_success(self) -> None:
        self.failures = 0
        self.state = "closed"

    def record_failure(self) -> None:
        self.failures += 1
        if self.failures >= self.failure_threshold:
            self.state = "open"

    def half_open(self) -> None:
        if self.state == "open":
            self.state = "half_open"
