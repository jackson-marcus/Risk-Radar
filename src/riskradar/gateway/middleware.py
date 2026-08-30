"""Gateway middleware: request ids, timing, and service-name injection."""

from __future__ import annotations

from time import perf_counter
from typing import Any
from uuid import uuid4


class GatewayMiddleware:
    def wrap(self, service: str, payload: dict[str, Any]) -> dict[str, Any]:
        started = perf_counter()
        envelope = {
            "request_id": uuid4().hex,
            "service": service,
            "payload": dict(payload),
        }
        envelope["elapsed_ms"] = (perf_counter() - started) * 1000.0
        return envelope
