"""In-process counters exported as Prometheus text."""

from __future__ import annotations

from collections import defaultdict


class MetricsRegistry:
    def __init__(self) -> None:
        self._counters: dict[tuple[str, str], int] = defaultdict(int)

    def inc(self, name: str, service: str, amount: int = 1) -> None:
        self._counters[(name, service)] += amount

    def value(self, name: str, service: str) -> int:
        return self._counters[(name, service)]

    def render(self) -> str:
        lines = ["# TYPE gateway_ok_total counter"]
        for (name, service), value in sorted(self._counters.items()):
            lines.append(f'{name}{{service="{service}"}} {value}')
        return "\n".join(lines) + "\n"
