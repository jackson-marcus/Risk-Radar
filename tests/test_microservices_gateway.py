"""Pattern #6 — Gateway → services → registry → observability."""

import pytest

from riskradar.gateway.circuit import CircuitBreaker
from riskradar.gateway.router import SERVICES, GatewayRouter


def test_router_dispatches_known_services():
    router = GatewayRouter()
    assert set(SERVICES) == set(router.handlers)
    result = router.dispatch(SERVICES[0], {"ping": True})
    assert result["result"]["ok"] is True
    assert router.metrics.value("gateway_ok_total", SERVICES[0]) == 1
    assert "gateway_ok_total" in router.metrics.render()


def test_unknown_service_is_rejected():
    with pytest.raises(KeyError):
        GatewayRouter().dispatch("not-a-service", {})


def test_circuit_opens_after_threshold():
    breaker = CircuitBreaker(failure_threshold=2)
    breaker.record_failure()
    assert breaker.allow()
    breaker.record_failure()
    assert breaker.state == "open" and not breaker.allow()
    breaker.half_open()
    breaker.record_success()
    assert breaker.state == "closed"


def test_open_circuit_rejects_dispatch():
    router = GatewayRouter()
    circuit = router.circuits[SERVICES[0]]
    circuit.state = "open"
    with pytest.raises(RuntimeError, match="circuit open"):
        router.dispatch(SERVICES[0], {})
