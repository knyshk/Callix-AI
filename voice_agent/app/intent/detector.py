# app/intent/detector.py

from app.core.errors_catalog import UNKNOWN_INTENT


def detect_intent(text: str):
    text = text.lower()

    if "balance" in text:
        return {"intent": "check_balance", "score": 0.9}

    if "agent" in text:
        return {"intent": "talk_to_agent", "score": 0.9}

    return UNKNOWN_INTENT
