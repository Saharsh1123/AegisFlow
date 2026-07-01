from app.db.session import SessionLocal
from sqlalchemy import select, delete
from app.db.models import Event
from uuid import UUID


def event_to_dict(db_event: Event) -> dict:
    return {
        "event_id": db_event.event_id,
        "status": db_event.status,
        "risk_approved": db_event.risk_approved,
        "risk_reason": db_event.risk_reason,
        "order_value": float(db_event.order_value),
        "created_at": db_event.created_at.isoformat().replace("+00:00", "Z"),
        "event_type": db_event.event_type,
        "asset": db_event.asset,
        "side": db_event.side,
        "quantity": db_event.quantity,
        "price": float(db_event.price),
    }


def save_event(event: dict):
    db = SessionLocal()

    try:
        db_event = Event(**event)

        db.add(db_event)
        db.commit()
        db.refresh(db_event)

        return event_to_dict(db_event)

    finally:
        db.close()


def get_event(event_id: str):
    db = SessionLocal()

    try:
        db_event = db.get(Event, event_id)

        if db_event is None:
            return None
        
        return event_to_dict(db_event)
    
    finally:
        db.close()


def get_all_events():
    db = SessionLocal()

    try:
        db_events = db.scalars(select(Event)).all()

        if db_events is None:
            return None
        
        return [event_to_dict(event) for event in db_events]

    finally:
        db.close()


def clear_one_event(event_id: UUID):
    db = SessionLocal()

    try:
        db_event = db.get(Event, event_id)

        if db_event is None:
            return False

        db.delete(db_event)
        db.commit()

        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def clear_events():
    db = SessionLocal()

    try:
        db.execute(delete(Event))
        db.commit()

    finally:
        db.close()