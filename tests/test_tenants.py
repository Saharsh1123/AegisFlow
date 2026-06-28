"""Tenant schema, service, persistence, and API behavior tests."""

from datetime import datetime, timezone
from uuid import UUID

from app.schemas.tenants import TenantCreateRequest
from app.services import tenant_service
from tests.helpers import (
    client,
    create_tenant,
    delete_one_tenant,
    delete_tenants,
    get_tenant,
    list_tenants,
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
    created_at = parse_timestamp(data["created_at"])

    assert response.status_code == 201
    assert set(data) == EXPECTED_TENANT_KEYS
    assert isinstance(UUID(data["tenant_id"]), UUID)
    assert isinstance(created_at, datetime)
    assert data["tenant_name"] == "Acme Capital"
    assert data["active"] is True


def test_tenant_service_generates_server_owned_fields(monkeypatch):
    captured = {}

    def capture_tenant(tenant):
        captured.update(tenant)
        return tenant

    monkeypatch.setattr(
        tenant_service.tenant_store,
        "save_tenant",
        capture_tenant,
    )

    tenant_service.create_tenant(
        TenantCreateRequest(tenant_name="Acme Capital")
    )

    assert isinstance(captured["tenant_id"], UUID)
    assert captured["active"] is True
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
    response = client.post("/tenants", json={})

    assert response.status_code == 422


def test_tenant_name_length_boundary_is_enforced():
    maximum_response = create_tenant({"tenant_name": "T" * 100})
    overlong_response = create_tenant({"tenant_name": "T" * 101})

    assert maximum_response.status_code == 201
    assert maximum_response.json()["tenant_name"] == "T" * 100
    assert overlong_response.status_code == 422


def test_duplicate_normalized_tenant_name_returns_409():
    create_tenant({"tenant_name": "Acme Capital"})

    response = create_tenant(
        {"tenant_name": "   Acme Capital   "}
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "tenant name already exists"
    }


def test_created_tenant_can_be_retrieved_without_data_loss():
    created = create_tenant(
        {"tenant_name": "Retrievable Tenant"}
    ).json()

    response = get_tenant(created["tenant_id"])

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_valid_tenant_id_returns_404():
    response = get_tenant(
        "00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "tenant not found"}


def test_delete_unknown_valid_tenant_id_returns_404():
    response = delete_one_tenant(
        "00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "tenant not found"}


def test_get_malformed_tenant_id_returns_422():
    response = get_tenant("not-a-uuid")

    assert response.status_code == 422


def test_delete_malformed_tenant_id_returns_422():
    response = delete_one_tenant("not-a-uuid")

    assert response.status_code == 422


def test_list_tenants_returns_empty_list_when_none_exist():
    response = list_tenants()

    assert response.status_code == 200
    assert response.json() == []


def test_list_tenants_returns_every_created_tenant():
    first = create_tenant(
        {"tenant_name": "Tenant One"}
    ).json()
    second = create_tenant(
        {"tenant_name": "Tenant Two"}
    ).json()

    response = list_tenants()
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2
    assert first in data
    assert second in data


def test_delete_one_tenant_removes_only_target():
    target = create_tenant(
        {"tenant_name": "Target Tenant"}
    ).json()
    survivor = create_tenant(
        {"tenant_name": "Survivor Tenant"}
    ).json()

    response = delete_one_tenant(target["tenant_id"])
    deleted_response = get_tenant(target["tenant_id"])
    survivor_response = get_tenant(survivor["tenant_id"])

    assert response.status_code == 204
    assert response.content == b""

    assert deleted_response.status_code == 404
    assert deleted_response.json() == {
        "detail": "tenant not found"
    }

    assert survivor_response.status_code == 200
    assert survivor_response.json() == survivor


def test_delete_all_tenants_removes_every_record_and_is_idempotent():
    create_tenant({"tenant_name": "Tenant One"})
    create_tenant({"tenant_name": "Tenant Two"})

    response = delete_tenants()
    list_response = list_tenants()
    repeated_response = delete_tenants()

    assert response.status_code == 204
    assert response.content == b""

    assert list_response.status_code == 200
    assert list_response.json() == []

    assert repeated_response.status_code == 204
    assert repeated_response.content == b""









