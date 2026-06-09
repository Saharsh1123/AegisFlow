from pydantic import BaseModel
from uuid import UUID

class TenantCreateRequest(BaseModel):
    tenant_name: str

class TenantResponse(BaseModel):
    tenant_id: UUID
    tenant_name: str
    active: bool
    created_at: str
    