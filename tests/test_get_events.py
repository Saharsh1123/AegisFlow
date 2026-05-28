import pytest
from fastapi.testclient import TestClient

from app.services.event_service import fake_db
from app.main import app
from tests.helpers import create_valid_event, get_valid_event


client = TestClient(app)

ID_FIELD = "event_id"


@pytest.fixture(autouse=True)
def clear_fake_db():
    fake_db.clear()
    yield
    fake_db.clear()


def test_get_valid_event_payload_is_successful():
    event_creation_response = create_valid_event()
    posted_data = event_creation_response.json()
    event_id = posted_data[ID_FIELD]

    get_event_response = get_valid_event(event_id)
    retrieved_data = get_event_response.json()

    assert get_event_response.status_code == 200
    assert retrieved_data[ID_FIELD] == event_id


def test_get_valid_event_returns_same_event_data():
    event_creation_response = create_valid_event()
    posted_data = event_creation_response.json()
    event_id = posted_data[ID_FIELD]

    get_event_response = get_valid_event(event_id)
    retrieved_data = get_event_response.json()

    assert get_event_response.status_code == 200
    assert retrieved_data == posted_data


def test_get_missing_event_returns_404():
    response = get_valid_event("fake-event-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "event not found"


def test_get_all_events_returns_empty_list_when_no_events_exist():
    response = client.get("/events")
    data = response.json()

    assert response.status_code == 200
    assert data == []


def test_get_all_events_returns_created_event():
    event_creation_response = create_valid_event()
    posted_data = event_creation_response.json()

    response = client.get("/events")
    data = response.json()

    assert response.status_code == 200
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0] == posted_data


def test_get_all_events_returns_multiple_created_events():
    first_response = create_valid_event({"asset": "AAPL"})
    second_response = create_valid_event({"asset": "MSFT"})

    first_event = first_response.json()
    second_event = second_response.json()

    response = client.get("/events")
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2
    assert first_event in data
    assert second_event in data


def test_created_event_id_can_be_used_to_retrieve_event():
    event_creation_response = create_valid_event()
    posted_data = event_creation_response.json()

    event_id = posted_data[ID_FIELD]

    response = client.get(f"/events/{event_id}")
    data = response.json()

    assert response.status_code == 200
    assert data[ID_FIELD] == event_id
    assert data == posted_data
