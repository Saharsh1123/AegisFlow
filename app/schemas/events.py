from pydantic import BaseModel, Field
from typing import Literal


class EventRequest(BaseModel):
    id: str | None=None
    event_type: str
    asset: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0)
    price: float = Field(gt=0)

