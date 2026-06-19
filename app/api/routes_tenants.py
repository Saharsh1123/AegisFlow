from fastapi import APIRouter, HTTPException
from app.schemas.tenants import TenantCreateRequest, TenantResponse
from app.services import tenant_service
from uuid import UUID


tenant_router = APIRouter()


@router.post("/tenants", status_code=201, response_model=TenantResponse)
def create_tenant(payload: TenantCreateRequest):
    return tenant_service.create_tenant(payload)


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(tenant_id: UUID):
    retrieved_tenant = tenant_service.get_tenant(tenant_id)
    if retrieved_tenant is None:
        raise HTTPException(status_code=404, detail="tenant not found")
    
    return retrieved_tenant


@router.get("/tenants", response_model=list[TenantResponse])
def get_all_tenants():
    return tenant_service.get_all_tenants()


@router.delete("/tenants/delete_all", response_model=TenantResponse)
def delete_all_tenants():
    tenant_service.clear_tenants()

