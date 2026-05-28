from uuid import UUID
from tests.helpers import make_valid_payload

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_valid_event_payload_returns_created_event():
    payload = make_valid_payload()

    response = client.post("/events", json=payload)
    data = response.json()

    assert response.status_code == 201

    assert set(data.keys()) == {
        "event_id",
        "status",
        "event_type",
        "asset",
        "side",
        "quantity",
        "price",
    }

    assert isinstance(data["event_id"], str)
    UUID(data["event_id"])

    assert data["status"] == "accepted"
    assert data["event_type"] == payload["event_type"]
    assert data["asset"] == payload["asset"]
    assert data["side"] == payload["side"]
    assert data["quantity"] == payload["quantity"]
    assert data["price"] == payload["price"]


@pytest.mark.parametrize("invalid_side", ["HOLD", "buy", "sell", "", "INVALID"])
def test_invalid_side_returns_422(invalid_side):
    payload = make_valid_payload({"side": invalid_side})

    response = client.post("/events", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("invalid_quantity", [0, -1, -100])
def test_invalid_quantity_returns_422(invalid_quantity):
    payload = make_valid_payload({"quantity": invalid_quantity})

    response = client.post("/events", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize("invalid_price", [0, -1, -192.5])
def test_invalid_price_returns_422(invalid_price):
    payload = make_valid_payload({"price": invalid_price})

    response = client.post("/events", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "missing_field",
    ["event_type", "asset", "side", "quantity", "price"],
)
def test_missing_required_field_returns_422(missing_field):
    payload = make_valid_payload()
    payload.pop(missing_field)

    response = client.post("/events", json=payload)

    assert response.status_code == 422