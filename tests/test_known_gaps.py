"""Strict expected-failure tests for known unfinished integration behavior.

These tests describe the intended public contract without changing application
logic. Because ``strict=True`` is used, pytest will fail with XPASS when a gap is
fixed, forcing the test to be promoted to the normal suite.
"""

import pytest

from tests.helpers import (
    client_without_server_exceptions,
    create_tenant,
    tenant_client_without_server_exceptions,
)


@pytest.mark.xfail(
    strict=True,
    reason="Tenant name length is enforced only by the DB and is not mapped to 422.",
)
def test_overlong_tenant_name_returns_422():
    response = tenant_client_without_server_exceptions.post(
        "/tenants",
        json={"tenant_name": "T" * 101},
    )

    assert response.status_code == 422


@pytest.mark.xfail(
    strict=True,
    reason=(
        "The tenant delete-all route is shadowed by /tenants/{tenant_id} and "
        "declares a response body it does not return."
    ),
)
def test_delete_all_tenants_endpoint_returns_204():
    create_tenant()

    response = tenant_client_without_server_exceptions.delete("/tenants/delete_all")

    assert response.status_code == 204


@pytest.mark.xfail(
    strict=True,
    reason=(
        "The event clear route is exposed at /tenants/delete_all and declares an "
        "EventResponse body it does not return."
    ),
)
def test_delete_all_events_endpoint_returns_204():
    # Seed storage directly because the POST /events response contract is unfinished.
    from tests.helpers import create_event_record

    create_event_record()

    response = client_without_server_exceptions.delete("/tenants/delete_all")

    assert response.status_code == 204
