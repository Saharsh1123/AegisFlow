from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

MAX_API_KEY_NAME_LENGTH = 100


class APIKeyCreateRequest(BaseModel):
    api_key_name: str

    @field_validator("api_key_name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("API key name must not be blank")

        if len(cleaned) > MAX_API_KEY_NAME_LENGTH:
            raise ValueError(
                f"API key name must be at most " f"{MAX_API_KEY_NAME_LENGTH} characters"
            )

        return cleaned


class APIKeyMetadataResponse(BaseModel):
    api_key_id: UUID
    tenant_id: UUID
    api_key_name: str
    created_at: datetime
    expires_at: datetime
    revoked_at: datetime | None


class APIKeyCreatedResponse(APIKeyMetadataResponse):
    api_key: str
