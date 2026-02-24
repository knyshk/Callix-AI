# app/core/logger.py

import datetime


def log_event(event_type: str, data: dict):
    timestamp = datetime.datetime.utcnow().isoformat()
    print(f"[{timestamp}] {event_type} - {data}")
