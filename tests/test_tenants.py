"""Tenant schema, service, storage, and isolated router tests."""

from datetime import datetime, timezone
from uuid import UUID

import pytest

from app.schemas.tenants import TenantCreateRequest
from app.services import tenant_service
from tests.helpers import (
    create_tenant,
    get_tenant,
    list_tenants,
    tenant_client,
)


EXPECTED_TENANT_KEYS = {
    "tenant_id",
    "tenant_name",
    "active",
    "created_at",
}


def parse_timestamp(timestamp: str) -> datetime:
    """Parse FastAPI's ISO-8601 timestamp representation."""

    return datetime.fromisoformat(timestamp.replace("Z", "+00:00"))


def test_create_tenant_returns_normalized_active_tenant():
    response = create_tenant({"tenant_name": "  Acme Capital  "})
    data = response.json()

    assert response.status_code == 201
    assert set(data) == EXPECTED_TENANT_KEYS
    UUID(data["tenant_id"])

    assert parse_timestamp(data["created_at"])

    assert data["tenant_name"] == "Acme Capital"
    assert data["active"] is True


def test_tenant_service_generates_timezone_aware_timestamp(monkeypatch):
    captured = {}

    def capture_tenant(tenant):
        captured.update(tenant)
        return tenant

    monkeypatch.setattr(tenant_service.tenant_store, "save_tenant", capture_tenant)

    tenant_service.create_tenant(TenantCreateRequest(tenant_name="Acme Capital"))

    assert captured["created_at"].tzinfo is not None
    assert captured["created_at"].utcoffset() == timezone.utc.utcoffset(
        captured["created_at"]
    )


def test_create_tenant_generates_unique_ids():
    first = create_tenant({"tenant_name": "Tenant One"}).json()
    second = create_tenant({"tenant_name": "Tenant Two"}).json()

    assert first["tenant_id"] != second["tenant_id"]


def test_whitespace_only_tenant_name_is_rejected():
    response = create_tenant({"tenant_name": "   "})

    assert response.status_code == 422



def test_non_string_tenant_name_is_rejected():
    response = create_tenant({"tenant_name": 123})

    assert response.status_code == 422

def test_tenant_name_is_required():
    response = tenant_client.post("/tenants", json={})

    assert response.status_code == 422


def test_created_tenant_can_be_retrieved_without_data_loss():
    created = create_tenant().json()

    response = get_tenant(created["tenant_id"])

    assert response.status_code == 200
    assert response.json() == created


def test_unknown_valid_tenant_id_returns_404():
    response = get_tenant("00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404
    assert response.json() == {"detail": "tenant not found"}


def test_malformed_tenant_id_returns_422():
    response = get_tenant("not-a-uuid")

    assert response.status_code == 422


def test_list_tenants_returns_empty_list_when_none_exist():
    response = list_tenants()

    assert response.status_code == 200
    assert response.json() == []


def test_list_tenants_returns_every_created_tenant():
    first = create_tenant({"tenant_name": "Tenant One"}).json()
    second = create_tenant({"tenant_name": "Tenant Two"}).json()

    response = list_tenants()
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2
    assert first in data
    assert second in data


def test_clear_tenants_service_removes_all_records():
    create_tenant({"tenant_name": "Tenant One"})
    create_tenant({"tenant_name": "Tenant Two"})

    tenant_service.clear_tenants()

    assert list_tenants().json() == []
