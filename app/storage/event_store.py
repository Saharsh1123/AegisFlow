fake_db = {}

def save_event(event_id: str, event: dict):
    fake_db[event_id] = event

def get_event(event_id: str):
    if event_id in fake_db:
        return fake_db[event_id]

    return None

def get_all_events():
    return list(fake_db.values())

def clear_events():
    fake_db.clear()