import pytest

from tests.helpers import create_valid_event, get_all_events, get_valid_event


def test_get_valid_event_payload_is_successful():
    event_creation_response = create_valid_event()
    posted_data = event_creation_response.json()
    event_id = posted_data["event_id"]

    get_event_response = get_valid_event(event_id)
    retrieved_data = get_event_response.json()

    assert get_event_response.status_code == 200
    assert retrieved_data["event_id"] == event_id


def test_get_valid_event_returns_same_event_data():
    event_creation_response = create_valid_event()
    posted_data = event_creation_response.json()
    event_id = posted_data["event_id"]

    get_event_response = get_valid_event(event_id)
    retrieved_data = get_event_response.json()

    assert get_event_response.status_code == 200
    assert retrieved_data == posted_data


def test_get_rejected_event_returns_same_rejected_event_data():
    event_creation_response = create_valid_event({"quantity": 11, "price": 5000.0})
    posted_data = event_creation_response.json()
    event_id = posted_data["event_id"]

    get_event_response = get_valid_event(event_id)
    retrieved_data = get_event_response.json()

    assert get_event_response.status_code == 200
    assert retrieved_data == posted_data
    assert retrieved_data["status"] == "rejected"
    assert retrieved_data["risk_approved"] is False
    assert retrieved_data["risk_reason"] == "MAX_ORDER_VALUE_EXCEEDED"


def test_get_missing_event_returns_404():
    response = get_valid_event("fake-event-id")

    assert response.status_code == 404
    assert response.json()["detail"] == "event not found"


def test_get_all_events_returns_empty_list_when_no_events_exist():
    response = get_all_events()
    data = response.json()

    assert response.status_code == 200
    assert data == []


def test_get_all_events_returns_created_event():
    event_creation_response = create_valid_event()
    posted_data = event_creation_response.json()

    response = get_all_events()
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

    response = get_all_events()
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2
    assert first_event in data
    assert second_event in data


def test_get_all_events_includes_accepted_and_rejected_events():
    accepted_response = create_valid_event({"quantity": 10, "price": 1000.0})
    rejected_response = create_valid_event({"quantity": 11, "price": 5000.0})

    accepted_event = accepted_response.json()
    rejected_event = rejected_response.json()

    response = get_all_events()
    data = response.json()

    assert response.status_code == 200
    assert len(data) == 2
    assert accepted_event in data
    assert rejected_event in data


def test_created_event_id_can_be_used_to_retrieve_event():
    event_creation_response = create_valid_event()
    posted_data = event_creation_response.json()

    event_id = posted_data["event_id"]

    response = get_valid_event(event_id)
    data = response.json()

    assert response.status_code == 200
    assert data["event_id"] == event_id
    assert data == posted_data


@pytest.mark.parametrize("event_id", ["not-a-real-id", "123"])
def test_invalid_or_unknown_event_ids_return_404(event_id):
    response = get_valid_event(event_id)

    assert response.status_code == 404