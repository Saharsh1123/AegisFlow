"""Health endpoint contract tests."""

from tests.helpers import client


def test_health_route_returns_exact_ok_contract():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
