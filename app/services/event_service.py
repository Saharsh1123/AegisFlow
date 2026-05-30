from app.schemas.events import EventRequest
from app.storage import event_store
from uuid import uuid4


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

    event_store.save_event(new_id, created_event)

    return created_event


def get_event(event_id: str):
    return event_store.get_event(event_id)

def get_all_events():
    return event_store.get_all_events()