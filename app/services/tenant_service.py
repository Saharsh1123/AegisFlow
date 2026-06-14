from app.schemas.tenants import TenantCreateRequest
from app.storage import tenant_store
from datetime import datetime, timezone
from uuid import uuid4


def create_tenant(payload: TenantCreateRequest):
    new_id = uuid4()

    tenant = {
        "tenant_id": new_id,
        "tenant_name": payload.tenant_name,
        "active": True,
        "created_at": datetime.now(timezone.utc)
    }

    return tenant_store.save_tenant(tenant)

def get_tenant(tenant_id: str):
    return tenant_store.get_tenant(tenant_id)

def get_all_tenants():
    return tenant_store.get_all_tenants()

def clear_tenants():
    tenant_store.clear_tenants()

