"""API-key schema contract tests."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas.api_keys import (
    APIKeyCreatedResponse,
    APIKeyCreateRequest,
    APIKeyMetadataResponse,
)


def make_api_key_metadata(**overrides):
    """Build valid API-key metadata response values."""

    now = datetime.now(timezone.utc)
    values = {
        "api_key_id": uuid4(),
        "tenant_id": uuid4(),
        "api_key_name": "production-ingestion",
        "created_at": now,
        "expires_at": now + timedelta(days=90),
        "revoked_at": None,
    }
    values.update(overrides)
    return values


def test_api_key_create_request_strips_surrounding_whitespace():
    request = APIKeyCreateRequest(api_key_name="  production-ingestion  ")

    assert request.api_key_name == "production-ingestion"


@pytest.mark.parametrize(
    "api_key_name",
    ["", "   "],
    ids=["empty", "whitespace"],
)
def test_api_key_create_request_rejects_blank_names(api_key_name):
    with pytest.raises(ValidationError):
        APIKeyCreateRequest(api_key_name=api_key_name)


def test_api_key_create_request_accepts_100_character_name():
    request = APIKeyCreateRequest(api_key_name="A" * 100)

    assert request.api_key_name == "A" * 100


def test_api_key_create_request_rejects_101_character_name():
    with pytest.raises(ValidationError):
        APIKeyCreateRequest(api_key_name="A" * 101)


def test_api_key_metadata_response_excludes_secret_material():
    response = APIKeyMetadataResponse(**make_api_key_metadata())

    serialized = response.model_dump()

    assert "api_key" not in serialized
    assert "secret_digest" not in serialized
    assert "hmac_key_version" not in serialized


def test_api_key_created_response_includes_raw_api_key_once():
    response = APIKeyCreatedResponse(
        **make_api_key_metadata(),
        api_key="agf_550e8400-e29b-41d4-a716-446655440000.example-secret",
    )

    assert response.api_key == "agf_550e8400-e29b-41d4-a716-446655440000.example-secret"


def test_api_key_created_response_requires_raw_api_key():
    with pytest.raises(ValidationError):
        APIKeyCreatedResponse(**make_api_key_metadata())


def test_api_key_created_response_still_excludes_internal_verifier_fields():
    response = APIKeyCreatedResponse(
        **make_api_key_metadata(),
        api_key="agf_550e8400-e29b-41d4-a716-446655440000.example-secret",
    )

    serialized = response.model_dump()

    assert "secret_digest" not in serialized
    assert "hmac_key_version" not in serialized
