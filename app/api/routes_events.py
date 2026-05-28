from fastapi import APIRouter, HTTPException
from app.schemas.events import EventRequest
from uuid import uuid4

fake_db = {}

router = APIRouter()

@router.post("/events", status_code=201)
def create_event(payload: EventRequest):
    new_id = str(uuid4())

    created_event = {
             "event_id": new_id, 
             "status": "accepted",
             "asset": payload.asset,
             "event_type": payload.event_type,
             "side": payload.side,
             "quantity": payload.quantity,
             "price": payload.price
           }

    fake_db[new_id] = created_event

    return created_event

@router.get("/events/{event_id}")
def get_event(event_id: str):
    if event_id in fake_db:
        return fake_db[event_id]

    raise HTTPException(status_code=404, detail="event not found")

@router.get("/events")
def get_all_events():
    return list(fake_db.values())