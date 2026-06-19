"""Event schema, service, persistence, and read-endpoint tests."""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.events import EventRequest
from app.services import event_service
from tests.helpers import (
    client,
    create_event_record,
    get_event,
    list_events,
    make_valid_event_payload,
    post_event,
)


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


def parse_timestamp(timestamp: str) -> datetime:
    """Parse FastAPI's ISO-8601 timestamp representation."""

    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def test_create_event_builds_complete_normalized_record():
    record = create_event_record({"asset": "  aapl  "})

    assert set(record) == EXPECTED_EVENT_KEYS
    assert isinstance(record["event_id"], UUID)
    assert record["created_at"].tzinfo is not None
    assert record["created_at"].utcoffset() == timezone.utc.utcoffset(
        record["created_at"]
    )
    assert record["status"] == "accepted"
    assert record["risk_approved"] is True
    assert record["risk_reason"] is None
    assert record["order_value"] == pytest.approx(1925.0)
    assert record["event_type"] == "ORDER_SUBMITTED"
    assert record["asset"] == "AAPL"
    assert record["side"] == "BUY"
    assert record["quantity"] == 10
    assert record["price"] == 192.5


def test_create_event_generates_unique_ids():
    first = create_event_record({"asset": "AAPL"})
    second = create_event_record({"asset": "MSFT"})

    assert first["event_id"] != second["event_id"]


@pytest.mark.parametrize(
    "event_type",
    [
        "ORDER_SUBMITTED",
        "ORDER_CANCELLED",
        "ORDER_FILLED",
        "RISK_CHECK_REQUESTED",
    ],
)
def test_each_supported_event_type_is_accepted(event_type):
    record = create_event_record({"event_type": event_type})

    assert record["event_type"] == event_type


def test_sell_side_is_supported():
    record = create_event_record({"side": "SELL"})

    assert record["side"] == "SELL"


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("event_type", "order_submitted"),
        ("side", "buy"),
    ],
)
def test_enum_fields_are_case_sensitive(field, invalid_value):
    payload = make_valid_event_payload({field: invalid_value})

    with pytest.raises(ValidationError):
        EventRequest(**payload)


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("quantity", 0),
        ("quantity", -1),
        ("price", 0),
        ("price", -0.01),
    ],
)
def test_non_positive_numeric_fields_are_rejected(field, invalid_value):
    response = post_event({field: invalid_value})

    assert response.status_code == 422


@pytest.mark.parametrize(
    "missing_field",
    ["event_type", "asset", "side", "quantity", "price"],
)
def test_each_required_event_field_is_enforced(missing_field):
    payload = make_valid_event_payload()
    payload.pop(missing_field)

    response = client.post("/events", json=payload)

    assert response.status_code == 422


@pytest.mark.parametrize(
    ("field", "invalid_value"),
    [
        ("quantity", "not-a-number"),
        ("price", "not-a-number"),
    ],
)
def test_non_numeric_quantity_and_price_are_rejected(field, invalid_value):
    response = post_event({field: invalid_value})

    assert response.status_code == 422



def test_non_string_asset_is_rejected():
    response = post_event({"asset": 123})

    assert response.status_code == 422

def test_whitespace_only_asset_is_rejected():
    response = post_event({"asset": "   "})

    assert response.status_code == 422


def test_asset_length_boundary_is_enforced():
    maximum = EventRequest(**make_valid_event_payload({"asset": "A" * 30}))

    with pytest.raises(ValidationError):
        EventRequest(**make_valid_event_payload({"asset": "A" * 31}))

    assert maximum.asset == "A" * 30


def test_order_equal_to_risk_limit_is_accepted():
    record = create_event_record({"quantity": 10, "price": 5000.0})

    assert record["order_value"] == pytest.approx(50000.0)
    assert record["status"] == "accepted"
    assert record["risk_approved"] is True
    assert record["risk_reason"] is None


def test_order_over_risk_limit_is_rejected_and_persisted():
    created = create_event_record({"quantity": 11, "price": 5000.0})

    response = get_event(str(created["event_id"]))
    retrieved = response.json()

    assert created["order_value"] == pytest.approx(55000.0)
    assert created["status"] == "rejected"
    assert created["risk_approved"] is False
    assert created["risk_reason"] == "MAX_ORDER_VALUE_EXCEEDED"
    assert response.status_code == 200
    assert retrieved["event_id"] == str(created["event_id"])
    assert retrieved["status"] == created["status"]
    assert retrieved["risk_approved"] is created["risk_approved"]
    assert retrieved["risk_reason"] == created["risk_reason"]


def test_created_event_can_be_retrieved_with_business_data_intact():
    created = create_event_record()

    response = get_event(str(created["event_id"]))
    retrieved = response.json()

    assert response.status_code == 200
    assert retrieved["event_id"] == str(created["event_id"])
    assert retrieved["event_type"] == created["event_type"]
    assert retrieved["asset"] == created["asset"]
    assert retrieved["side"] == created["side"]
    assert retrieved["quantity"] == created["quantity"]
    assert retrieved["price"] == created["price"]
    assert retrieved["order_value"] == created["order_value"]
    assert parse_timestamp(retrieved["created_at"])


def test_unknown_valid_event_id_returns_404():
    response = get_event("00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "event not found"}


def test_list_events_returns_empty_list_when_no_events_exist():
    response = list_events()

    assert response.status_code == 200
    assert response.json() == []


def test_list_events_returns_all_accepted_and_rejected_records():
    accepted = create_event_record({"asset": "AAPL"})
    rejected = create_event_record(
        {"asset": "MSFT", "quantity": 11, "price": 5000.0}
    )

    response = list_events()
    data = response.json()
    returned_ids = {item["event_id"] for item in data}

    assert response.status_code == 200
    assert len(data) == 2
    assert returned_ids == {str(accepted["event_id"]), str(rejected["event_id"])}
    assert {item["status"] for item in data} == {"accepted", "rejected"}


def test_clear_events_service_removes_all_records():
    create_event_record({"asset": "AAPL"})
    create_event_record({"asset": "MSFT"})

    event_service.clear_events()

    assert list_events().json() == []
