from datetime import datetime, timezone
from uuid import UUID

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.storage import event_store
from tests.helpers import make_valid_payload


client = TestClient(app)


@pytest.fixture(autouse=True)
def clear_fake_db():
    event_store.clear_events()
    yield
    event_store.clear_events()


def parse_created_at(timestamp: str) -> datetime:
    if timestamp.endswith("Z"):
        timestamp = timestamp.replace("Z", "+00:00")

    return datetime.fromisoformat(timestamp)


def test_valid_event_payload_returns_created_event():
    payload = make_valid_payload()

    response = client.post("/events", json=payload)
    data = response.json()

    assert response.status_code == 201

    assert set(data.keys()) == {
        "event_id",
        "status",
        "created_at",
        "event_type",
        "asset",
        "side",
        "quantity",
        "price",
    }

    assert isinstance(data["event_id"], str)
    UUID(data["event_id"])

    assert isinstance(data["created_at"], str)
    assert data["created_at"] != ""

    parsed_created_at = parse_created_at(data["created_at"])
    assert parsed_created_at.tzinfo is not None
    assert parsed_created_at.utcoffset() == timezone.utc.utcoffset(parsed_created_at)

    assert data["status"] == "accepted"
    assert data["event_type"] == payload["event_type"]
    assert data["asset"] == payload["asset"]
    assert data["side"] == payload["side"]
    assert data["quantity"] == payload["quantity"]
    assert data["price"] == payload["price"]


def test_created_event_has_unique_event_id_each_time():
    first_response = client.post("/events", json=make_valid_payload({"asset": "AAPL"}))
    second_response = client.post("/events", json=make_valid_payload({"asset": "MSFT"}))

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_data["event_id"] != second_data["event_id"]


def test_created_event_has_created_at_each_time():
    response = client.post("/events", json=make_valid_payload())
    data = response.json()

    assert response.status_code == 201
    assert "created_at" in data
    assert isinstance(data["created_at"], str)
    assert data["created_at"] != ""


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