from datetime import datetime, timezone
from uuid import UUID

import pytest

from tests.helpers import client, create_valid_event, make_valid_payload


EXPECTED_EVENT_KEYS = {
    "event_id",
    "status",
    "risk_approved",
    "risk_reason",
    "order_value",
    "created_at",
    "event_type",
    "asset",
    "side",
    "quantity",
    "price",
}


def parse_created_at(timestamp: str) -> datetime:
    if timestamp.endswith("Z"):
        timestamp = timestamp.replace("Z", "+00:00")

    return datetime.fromisoformat(timestamp)


def test_valid_event_payload_returns_created_event():
    payload = make_valid_payload()

    response = create_valid_event()
    data = response.json()

    assert response.status_code == 201
    assert set(data.keys()) == EXPECTED_EVENT_KEYS

    assert isinstance(data["event_id"], str)
    UUID(data["event_id"])

    assert isinstance(data["created_at"], str)
    assert data["created_at"] != ""

    parsed_created_at = parse_created_at(data["created_at"])
    assert parsed_created_at.tzinfo is not None
    assert parsed_created_at.utcoffset() == timezone.utc.utcoffset(parsed_created_at)

    assert data["status"] == "accepted"
    assert data["risk_approved"] is True
    assert data["risk_reason"] is None
    assert data["order_value"] == pytest.approx(payload["quantity"] * payload["price"])

    assert data["event_type"] == payload["event_type"]
    assert data["asset"] == payload["asset"]
    assert data["side"] == payload["side"]
    assert data["quantity"] == payload["quantity"]
    assert data["price"] == payload["price"]


def test_created_event_has_unique_event_id_each_time():
    first_response = create_valid_event({"asset": "AAPL"})
    second_response = create_valid_event({"asset": "MSFT"})

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_response.status_code == 201
    assert second_response.status_code == 201
    assert first_data["event_id"] != second_data["event_id"]


def test_created_event_has_created_at_each_time():
    response = create_valid_event()
    data = response.json()

    assert response.status_code == 201
    assert "created_at" in data
    assert isinstance(data["created_at"], str)
    assert data["created_at"] != ""


def test_order_value_is_quantity_times_price():
    payload = make_valid_payload({"quantity": 7, "price": 123.45})

    response = create_valid_event({"quantity": 7, "price": 123.45})
    data = response.json()

    assert response.status_code == 201
    assert data["order_value"] == pytest.approx(payload["quantity"] * payload["price"])


def test_order_under_max_order_value_is_accepted():
    response = create_valid_event({"quantity": 10, "price": 1000.0})
    data = response.json()

    assert response.status_code == 201
    assert data["order_value"] == pytest.approx(10000.0)
    assert data["status"] == "accepted"
    assert data["risk_approved"] is True
    assert data["risk_reason"] is None


def test_order_equal_to_max_order_value_is_accepted():
    response = create_valid_event({"quantity": 10, "price": 5000.0})
    data = response.json()

    assert response.status_code == 201
    assert data["order_value"] == pytest.approx(50000.0)
    assert data["status"] == "accepted"
    assert data["risk_approved"] is True
    assert data["risk_reason"] is None


def test_order_over_max_order_value_is_rejected():
    response = create_valid_event({"quantity": 11, "price": 5000.0})
    data = response.json()

    assert response.status_code == 201
    assert data["order_value"] == pytest.approx(55000.0)
    assert data["status"] == "rejected"
    assert data["risk_approved"] is False
    assert data["risk_reason"] == "MAX_ORDER_VALUE_EXCEEDED"


@pytest.mark.parametrize("invalid_side", ["HOLD", "buy", "sell", "", "INVALID"])
def test_invalid_side_returns_422(invalid_side):
    response = create_valid_event({"side": invalid_side})

    assert response.status_code == 422


@pytest.mark.parametrize("invalid_quantity", [0, -1, -100])
def test_invalid_quantity_returns_422(invalid_quantity):
    response = create_valid_event({"quantity": invalid_quantity})

    assert response.status_code == 422


@pytest.mark.parametrize("invalid_price", [0, -1, -192.5])
def test_invalid_price_returns_422(invalid_price):
    response = create_valid_event({"price": invalid_price})

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


@pytest.mark.parametrize(
    ("raw_asset", "expected_asset"),
    [
        ("aapl", "AAPL"),
        ("AaPl", "AAPL"),
        ("msft", "MSFT"),
        ("GOOG", "GOOG"),
    ],
)
def test_asset_is_normalized_to_uppercase(raw_asset, expected_asset):
    response = create_valid_event({"asset": raw_asset})
    data = response.json()

    assert response.status_code == 201
    assert data["asset"] == expected_asset


@pytest.mark.parametrize("invalid_asset", ["", "   "])
def test_blank_asset_returns_422(invalid_asset):
    response = create_valid_event({"asset": invalid_asset})

    assert response.status_code == 422