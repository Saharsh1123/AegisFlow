from app.schemas.tenants import TenantCreateRequest
from app.storage import tenant_store
from datetime import datetime, timezone
from fastapi import HTTPException
from uuid import uuid4, UUID


def create_tenant(payload: TenantCreateRequest):
    new_id = uuid4()

    existing_tenant = tenant_store.get_tenant_by_name(payload.tenant_name)

    if existing_tenant is not None:
        raise HTTPException(status_code=409, detail="tenant name already exists")

    tenant = {
        "tenant_id": new_id,
        "tenant_name": payload.tenant_name,
        "active": True,
        "created_at": datetime.now(timezone.utc)
    }

    return tenant_store.save_tenant(tenant)

def get_tenant_by_id(tenant_id: UUID):
    return tenant_store.get_tenant_by_id(tenant_id)

def get_all_tenants():
    return tenant_store.get_all_tenants()

def clear_tenants():
    tenant_store.clear_tenants()

