from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

def make_valid_payload(overrides=None):
    payload = {
        "event_type": "ORDER_SUBMITTED",
        "asset": "AAPL",
        "side": "BUY",
        "quantity": 10,
        "price": 192.5,
    }

    if overrides:
        payload.update(overrides)

    return payload

def create_valid_event(overrides=None):
    payload = make_valid_payload(overrides)
    return client.post("/events", json=payload)

def get_valid_event(event_id):
    return client.get(f"/events/{event_id}")
