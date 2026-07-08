"""Database-level API-key integrity tests that bypass Pydantic validation."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.models import APIKey, Tenant

VALID_SECRET_DIGEST = "a" * 64


def make_tenant_model(**overrides) -> Tenant:
    """Build a valid ORM tenant for direct database tests."""

    values = {
        "tenant_id": uuid4(),
        "tenant_name": f"Tenant {uuid4()}",
        "active": True,
        "created_at": datetime.now(timezone.utc),
    }
    values.update(overrides)
    return Tenant(**values)


def make_api_key_model(**overrides) -> APIKey:
    """Build a valid ORM API key for direct database tests."""

    now = datetime.now(timezone.utc)
    values = {
        "api_key_id": uuid4(),
        "tenant_id": uuid4(),
        "api_key_name": f"Key {uuid4()}",
        "secret_digest": VALID_SECRET_DIGEST,
        "hmac_key_version": 1,
        "created_at": now,
        "expires_at": now + timedelta(days=90),
        "revoked_at": None,
    }
    values.update(overrides)
    return APIKey(**values)


def persist_tenant(db_session, **overrides) -> Tenant:
    """Persist a tenant and return it for API-key foreign-key tests."""

    tenant = make_tenant_model(**overrides)
    db_session.add(tenant)
    db_session.flush()
    return tenant


def test_api_key_allows_multiple_keys_for_same_tenant(db_session):
    tenant = persist_tenant(db_session)
    first_key = make_api_key_model(
        tenant_id=tenant.tenant_id,
        api_key_name="production-ingestion",
    )
    second_key = make_api_key_model(
        tenant_id=tenant.tenant_id,
        api_key_name="staging-ingestion",
    )

    db_session.add_all([first_key, second_key])
    db_session.commit()

    statement = select(APIKey).where(APIKey.tenant_id == tenant.tenant_id)
    stored_keys = db_session.scalars(statement).all()

    assert {key.api_key_id for key in stored_keys} == {
        first_key.api_key_id,
        second_key.api_key_id,
    }


def test_api_key_tenant_id_must_reference_existing_tenant(db_session):
    db_session.add(make_api_key_model())

    with pytest.raises(IntegrityError):
        db_session.flush()


@pytest.mark.parametrize(
    "api_key_name",
    ["", "A" * 101],
    ids=["empty", "overlong"],
)
def test_api_key_name_length_constraint_rejects_invalid_names(
    db_session,
    api_key_name,
):
    tenant = persist_tenant(db_session)
    db_session.add(
        make_api_key_model(
            tenant_id=tenant.tenant_id,
            api_key_name=api_key_name,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_api_key_name_length_constraint_accepts_100_character_name(db_session):
    tenant = persist_tenant(db_session)
    api_key = make_api_key_model(
        tenant_id=tenant.tenant_id,
        api_key_name="A" * 100,
    )

    db_session.add(api_key)
    db_session.commit()

    assert api_key.api_key_name == "A" * 100


@pytest.mark.parametrize(
    "secret_digest",
    ["", "a" * 63, "a" * 65],
    ids=["empty", "short", "long"],
)
def test_api_key_secret_digest_length_constraint_rejects_invalid_lengths(
    db_session,
    secret_digest,
):
    tenant = persist_tenant(db_session)
    db_session.add(
        make_api_key_model(
            tenant_id=tenant.tenant_id,
            secret_digest=secret_digest,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


@pytest.mark.parametrize("hmac_key_version", [0, -1], ids=["zero", "negative"])
def test_api_key_hmac_key_version_constraint_requires_positive_value(
    db_session,
    hmac_key_version,
):
    tenant = persist_tenant(db_session)
    db_session.add(
        make_api_key_model(
            tenant_id=tenant.tenant_id,
            hmac_key_version=hmac_key_version,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_api_key_hmac_key_version_defaults_to_one(db_session):
    tenant = persist_tenant(db_session)
    api_key = make_api_key_model(tenant_id=tenant.tenant_id)
    api_key.hmac_key_version = None

    db_session.add(api_key)
    db_session.commit()
    db_session.refresh(api_key)

    assert api_key.hmac_key_version == 1


@pytest.mark.parametrize(
    "expires_at_offset",
    [timedelta(days=-1), timedelta(0)],
    ids=["before-created", "same-as-created"],
)
def test_api_key_expires_at_must_be_after_created_at(
    db_session,
    expires_at_offset,
):
    tenant = persist_tenant(db_session)
    created_at = datetime.now(timezone.utc)
    db_session.add(
        make_api_key_model(
            tenant_id=tenant.tenant_id,
            created_at=created_at,
            expires_at=created_at + expires_at_offset,
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_api_key_revoked_at_cannot_be_before_created_at(db_session):
    tenant = persist_tenant(db_session)
    created_at = datetime.now(timezone.utc)
    db_session.add(
        make_api_key_model(
            tenant_id=tenant.tenant_id,
            created_at=created_at,
            revoked_at=created_at - timedelta(seconds=1),
        )
    )

    with pytest.raises(IntegrityError):
        db_session.flush()


def test_api_key_revoked_at_may_equal_created_at(db_session):
    tenant = persist_tenant(db_session)
    created_at = datetime.now(timezone.utc)
    api_key = make_api_key_model(
        tenant_id=tenant.tenant_id,
        created_at=created_at,
        expires_at=created_at + timedelta(days=90),
        revoked_at=created_at,
    )

    db_session.add(api_key)
    db_session.commit()

    assert api_key.revoked_at is not None
