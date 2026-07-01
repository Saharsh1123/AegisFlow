"""Reusable request builders and test clients."""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routes_tenants import tenant_router
from app.main import app
from app.schemas.events import EventRequest
from app.services import event_service
from uuid import UUID


client = TestClient(app)
client_without_server_exceptions = TestClient(app, raise_server_exceptions=False)

tenant_app = FastAPI()
tenant_app.include_router(tenant_router)
tenant_client = TestClient(tenant_app)
tenant_client_without_server_exceptions = TestClient(
    tenant_app,
    raise_server_exceptions=False,
)


def make_valid_event_payload(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return a valid event request, optionally replacing selected fields."""

    payload: dict[str, Any] = {
        "event_type": "ORDER_SUBMITTED",
        "asset": "AAPL",
        "side": "BUY",
        "quantity": 10,
        "price": 192.5,
    }

    if overrides:
        payload.update(overrides)

    return payload


def post_event(overrides: dict[str, Any] | None = None):
    """POST an event payload through the public API."""

    return client.post("/events", json=make_valid_event_payload(overrides))


def create_event_record(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    """Create and persist an event through the schema and service layers."""

    payload = EventRequest(**make_valid_event_payload(overrides))
    return event_service.create_event(payload)


def get_event(event_id: UUID):
    """Retrieve an event through the public API."""

    return client.get(f"/events/{event_id}")


def list_events():
    """List all persisted events through the public API."""

    return client.get("/events")


def delete_events():
    return client.delete("/events/delete_all")


def delete_one_event(event_id: UUID):
    return client.delete(f"/events/delete/{event_id}")


def make_valid_tenant_payload(
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a valid tenant request, optionally replacing selected fields."""

    payload: dict[str, Any] = {"tenant_name": "Acme Capital"}

    if overrides:
        payload.update(overrides)

    return payload


def create_tenant(overrides: dict[str, Any] | None = None):
    """POST a tenant to the isolated tenant router application."""

    return tenant_client.post(
        "/tenants",
        json=make_valid_tenant_payload(overrides),
    )


def get_tenant(tenant_id: str):
    """Retrieve a tenant through the isolated tenant router application."""

    return tenant_client.get(f"/tenants/{tenant_id}")


def list_tenants():
    """List tenants through the isolated tenant router application."""

    return tenant_client.get("/tenants")


def delete_tenants():
    return tenant_client.delete("/tenants/delete_all")


def delete_one_tenant(tenant_id: UUID):
    return tenant_client.delete(f"/tenants/delete/{tenant_id}")
