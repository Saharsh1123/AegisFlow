from fastapi import APIRouter
from app.schemas.events import EventRequest
from uuid import uuid4

fake_db = {}

router = APIRouter()

@router.post("/events", status_code=201)
def create_event(payload: EventRequest):
    new_id = str(uuid4())

    fake_db[new_id] = {
        "event_type": payload.event_type,
        "asset": payload.asset,
        "side": payload.side,
        "quantity": payload.quantity,
        "price": payload.price
    }

    return {
             "id": new_id, 
             "status": "accepted",
             "asset": payload.asset,
             "event_type": payload.event_type,
             "side": payload.side,
             "quantity": payload.quantity,
             "price": payload.price
           }