"""Database-level integrity tests that bypass Pydantic validation."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import Event, Tenant


def make_event_model(**overrides) -> Event:
    """Build a valid ORM event for direct database tests."""

    values = {
        "event_id": uuid4(),
        "status": "accepted",
        "created_at": datetime.now(timezone.utc),
        "risk_approved": True,
        "risk_reason": None,
        "order_value": Decimal("100.000000"),
        "event_type": "ORDER_SUBMITTED",
        "asset": "AAPL",
        "side": "BUY",
        "quantity": 1,
        "price": Decimal("100.000000"),
    }
    values.update(overrides)
    return Event(**values)


def make_tenant_model(**overrides) -> Tenant:
    """Build a valid ORM tenant for direct database tests."""

    values = {
        "tenant_id": uuid4(),
        "tenant_name": "Acme Capital",
        "active": True,
        "created_at": datetime.now(timezone.utc),
    }
    values.update(overrides)
    return Tenant(**values)


@pytest.mark.parametrize(
    "overrides",
    [
        {"status": "pending"},
        {"side": "HOLD"},
        {"quantity": 0},
        {"order_value": Decimal("0")},
        {"price": Decimal("0")},
        {"event_type": "UNKNOWN"},
        {"asset": ""},
        {"asset": "A" * 31},
    ],
    ids=[
        "status",
        "side",
        "quantity",
        "order-value",
        "price",
        "event-type",
        "asset-empty",
        "asset-length",
    ],
)
def test_event_check_constraints_reject_invalid_rows(db_session, overrides):
    db_session.add(make_event_model(**overrides))

    with pytest.raises(IntegrityError):
        db_session.flush()


@pytest.mark.parametrize("invalid_name", ["", "T" * 101], ids=["empty", "overlong"])
def test_tenant_name_length_constraint_rejects_invalid_name(db_session, invalid_name):
    db_session.add(make_tenant_model(tenant_name=invalid_name))

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_tenant_name_unique_constraint_rejects_duplicate_names(db_session):
    db_session.add(make_tenant_model())
    db_session.commit()
    db_session.add(make_tenant_model())

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_tenant_active_defaults_to_true(db_session):
    tenant = Tenant(
        tenant_id=uuid4(),
        tenant_name="Acme Capital",
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(tenant)
    db_session.commit()
    db_session.refresh(tenant)

    assert tenant.active is True
