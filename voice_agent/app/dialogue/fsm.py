# app/dialogue/fsm.py

from app.core.errors import VoiceError


def handle_pipeline(stt_result, intent_result):
    if isinstance(stt_result, VoiceError):
        return {"response": stt_result.message}

    if isinstance(intent_result, VoiceError):
        return {"response": intent_result.message}

    return {
        "response": f"Intent detected: {intent_result['intent']}"
    }
