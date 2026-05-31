import pytest

from app.storage import event_store


@pytest.fixture(autouse=True)
def clear_fake_db():
    event_store.clear_events()
    yield
    event_store.clear_events()