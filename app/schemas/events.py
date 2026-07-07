from typing import Literal
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class EventRequest(BaseModel):
    event_type: Literal[
        "ORDER_SUBMITTED", "ORDER_CANCELLED", "ORDER_FILLED", "RISK_CHECK_REQUESTED"
    ]
    asset: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

    @field_validator("asset")
    @classmethod
    def normalize_asset(cls, value: str) -> str:
        MAX_ASSET_LENGTH = 30

        cleaned = value.strip()

        if not cleaned:
            raise ValueError("No asset specified")

        if len(cleaned) > MAX_ASSET_LENGTH:
            raise ValueError("Asset symbol too long")

        return cleaned.upper()


class EventResponse(BaseModel):
    event_id: UUID
    status: str
    created_at: datetime
    risk_approved: bool
    risk_reason: str | None
    order_value: float = Field(gt=0)
    event_type: Literal[
        "ORDER_SUBMITTED", "ORDER_CANCELLED", "ORDER_FILLED", "RISK_CHECK_REQUESTED"
    ]
    asset: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)
