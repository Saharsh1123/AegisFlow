from fastapi import APIRouter, HTTPException
from app.schemas.events import EventRequest
from app.services import event_service

router = APIRouter()

@router.post("/events", status_code=201)
def create_event(payload: EventRequest):
    return event_service.create_event(payload)

@router.get("/events")
def get_all_events():
    return event_service.get_all_events()

@router.get("/events/{event_id}")
def get_event(event_id: str):
    retrieved_event = event_service.get_event(event_id)
    if retrieved_event is None:
        raise HTTPException(status_code=404, detail="event not found")
    
    return retrieved_event
   