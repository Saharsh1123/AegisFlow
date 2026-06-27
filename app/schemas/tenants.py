from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID

class TenantCreateRequest(BaseModel):
    tenant_name: str

    @field_validator("tenant_name")
    @classmethod
    def normalize_tenant_name(cls, value: str) -> str:
        MAX_TENANT_NAME = 100
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("No tenant name specified")
        
        if len(cleaned) > MAX_TENANT_NAME:
            raise ValueError("Tenant name is too long")

        return cleaned


class TenantResponse(BaseModel):
    tenant_id: UUID
    tenant_name: str
    active: bool
    created_at: datetime
    