from pydantic import BaseModel, Field
from typing import Literal


class EventRequest(BaseModel):
    event_id: str | None=None
    event_type: str
    asset: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)


class EventResponse(BaseModel):
    event_id: str
    status: str
    created_at: str
    event_type: str
    asset: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

