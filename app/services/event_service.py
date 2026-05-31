from app.schemas.events import EventRequest
from app.storage import event_store
from app.services import risk_service
from datetime import datetime, timezone
from uuid import uuid4


def create_event(payload: EventRequest):
    new_id = str(uuid4())
    price = payload.price
    quantity = payload.quantity
    order_value = price * quantity

    approved, reason = risk_service.evaluate_risk(price, quantity, order_value)
    status = "rejected"
    if approved:
        status = "accepted"

    created_event = {
            "event_id": new_id, 
            "status": status,
            "risk_approved": approved,
            "risk_reason": reason,
            "order_value": order_value,
            "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "asset": payload.asset,
            "event_type": payload.event_type,
            "side": payload.side,
            "quantity": quantity,
            "price": price
           }

    event_store.save_event(new_id, created_event)

    return created_event


def get_event(event_id: str):
    return event_store.get_event(event_id)

def get_all_events():
    return event_store.get_all_events()