"""Lightweight span tracer for gateway hops."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Span:
    name: str
    request_id: str
    status: str = "in_progress"
    baggage: dict[str, str] = field(default_factory=dict)

    def finish(self, status: str) -> None:
        self.status = status


class Tracer:
    def __init__(self) -> None:
        self.spans: list[Span] = []

    def start(self, name: str, request_id: str) -> Span:
        span = Span(name=name, request_id=request_id)
        self.spans.append(span)
        return span
