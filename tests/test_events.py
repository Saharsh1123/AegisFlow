"""Event schema, service, persistence, risk, and API behavior tests."""

from datetime import datetime, timezone
from uuid import UUID

import pytest
from pydantic import ValidationError

from app.schemas.events import EventRequest
from app.services import event_service
from tests.helpers import (
    client,
    create_event_record,
    delete_events,
    delete_one_event,
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


def test_post_event_returns_complete_normalized_record():
    response = post_event({"asset": "  aapl  "})
    data = response.json()
    event_id = UUID(data["event_id"])
    created_at = parse_timestamp(data["created_at"])

    assert response.status_code == 201
    assert set(data) == EXPECTED_EVENT_KEYS
    assert isinstance(event_id, UUID)
    assert isinstance(created_at, datetime)

    assert data["status"] == "accepted"
    assert data["risk_approved"] is True
    assert data["risk_reason"] is None
    assert data["order_value"] == pytest.approx(1925.0)
    assert data["event_type"] == "ORDER_SUBMITTED"
    assert data["asset"] == "AAPL"
    assert data["side"] == "BUY"
    assert data["quantity"] == 10
    assert data["price"] == pytest.approx(192.5)


def test_event_service_generates_server_owned_fields():
    record = create_event_record()

    assert isinstance(record["event_id"], UUID)
    assert record["created_at"].tzinfo is not None
    assert record["created_at"].utcoffset() == timezone.utc.utcoffset(
        record["created_at"]
    )


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
    maximum_response = post_event({"asset": "A" * 30})
    overlong_response = post_event({"asset": "A" * 31})

    assert maximum_response.status_code == 201
    assert maximum_response.json()["asset"] == "A" * 30
    assert overlong_response.status_code == 422


def test_order_equal_to_risk_limit_is_accepted():
    record = create_event_record({"quantity": 10, "price": 5000.0})

    assert record["order_value"] == pytest.approx(50000.0)
    assert record["status"] == "accepted"
    assert record["risk_approved"] is True
    assert record["risk_reason"] is None


def test_order_over_risk_limit_is_rejected_and_persisted():
    created = create_event_record(
        {"quantity": 11, "price": 5000.0}
    )

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
    created_at = parse_timestamp(retrieved["created_at"])

    assert response.status_code == 200
    assert retrieved["event_id"] == str(created["event_id"])
    assert retrieved["event_type"] == created["event_type"]
    assert retrieved["asset"] == created["asset"]
    assert retrieved["side"] == created["side"]
    assert retrieved["quantity"] == created["quantity"]
    assert retrieved["price"] == pytest.approx(created["price"])
    assert retrieved["order_value"] == pytest.approx(
        created["order_value"]
    )
    assert isinstance(created_at, datetime)


def test_get_unknown_valid_event_id_returns_404():
    response = get_event(
        "00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "event not found"}


def test_get_malformed_event_id_returns_422_before_service(monkeypatch):
    """Malformed UUIDs should be rejected before event lookup runs."""

    def fail_if_called(*args, **kwargs):
        raise AssertionError(
            "event_service.get_event should not be called"
        )

    monkeypatch.setattr(
        event_service,
        "get_event",
        fail_if_called,
    )

    response = get_event("not-a-uuid")

    assert response.status_code == 422


def test_delete_unknown_valid_event_id_returns_404():
    response = delete_one_event(
        "00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "event not found"}


def test_delete_malformed_event_id_returns_422():
    response = delete_one_event("not-a-uuid")

    assert response.status_code == 422


def test_list_events_returns_empty_list_when_no_events_exist():
    response = list_events()

    assert response.status_code == 200
    assert response.json() == []


def test_list_events_returns_all_accepted_and_rejected_records():
    accepted = create_event_record({"asset": "AAPL"})
    rejected = create_event_record(
        {
            "asset": "MSFT",
            "quantity": 11,
            "price": 5000.0,
        }
    )

    response = list_events()
    data = response.json()
    returned_ids = {item["event_id"] for item in data}

    assert response.status_code == 200
    assert len(data) == 2
    assert returned_ids == {
        str(accepted["event_id"]),
        str(rejected["event_id"]),
    }
    assert {item["status"] for item in data} == {
        "accepted",
        "rejected",
    }


def test_delete_one_event_removes_only_target():
    target = create_event_record({"asset": "TARGET"})
    survivor = create_event_record({"asset": "SURVIVOR"})

    response = delete_one_event(str(target["event_id"]))
    deleted_response = get_event(str(target["event_id"]))
    survivor_response = get_event(str(survivor["event_id"]))
    survivor_data = survivor_response.json()

    assert response.status_code == 204
    assert response.content == b""

    assert deleted_response.status_code == 404
    assert deleted_response.json() == {
        "detail": "event not found"
    }

    assert survivor_response.status_code == 200
    assert survivor_data["event_id"] == str(survivor["event_id"])
    assert survivor_data["asset"] == survivor["asset"]
    assert survivor_data["event_type"] == survivor["event_type"]
    assert survivor_data["side"] == survivor["side"]
    assert survivor_data["quantity"] == survivor["quantity"]
    assert survivor_data["price"] == pytest.approx(
        survivor["price"]
    )
    assert survivor_data["status"] == survivor["status"]


def test_delete_all_events_removes_every_record_and_is_idempotent():
    create_event_record({"asset": "AAPL"})
    create_event_record({"asset": "MSFT"})

    response = delete_events()
    list_response = list_events()
    repeated_response = delete_events()

    assert response.status_code == 204
    assert response.content == b""

    assert list_response.status_code == 200
    assert list_response.json() == []

    assert repeated_response.status_code == 204
    assert repeated_response.content == b""


