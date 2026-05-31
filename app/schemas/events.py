from typing import Literal

from pydantic import BaseModel, Field, field_validator


class EventRequest(BaseModel):
    event_type: str
    asset: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

    @field_validator("asset")
    @classmethod
    def normalize_asset(cls, value: str) -> str:
        cleaned = value.strip()

        if not cleaned:
            raise ValueError("No asset specified")

        return cleaned.upper()


class EventResponse(BaseModel):
    event_id: str
    status: str
    created_at: str
    risk_approved: bool
    risk_reason: str | None
    order_value: float = Field(gt=0)
    event_type: str
    asset: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

