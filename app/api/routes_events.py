from fastapi import APIRouter, HTTPException, Response, status
from app.schemas.events import EventRequest, EventResponse
from app.services import event_service
from uuid import UUID

router = APIRouter()


@router.post("/events", status_code=201, response_model=EventResponse)
def create_event(payload: EventRequest):
    return event_service.create_event(payload)


@router.get("/events", response_model=list[EventResponse])
def get_all_events():
    return event_service.get_all_events()


@router.get("/events/{event_id}", response_model=EventResponse)
def get_event(event_id: UUID):
    retrieved_event = event_service.get_event(event_id)
    if retrieved_event is None:
        raise HTTPException(status_code=404, detail="event not found")
    
    return retrieved_event
   

@router.delete(
    "/events/delete_all",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
def delete_all_events() -> Response:
    event_service.clear_events()
    return Response(status_code=status.HTTP_204_NO_CONTENT)