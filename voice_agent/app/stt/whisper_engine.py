# app/stt/whisper_engine.py

from app.core.errors_catalog import NO_INPUT, LOW_CONFIDENCE_STT
from app.core.errors import VoiceError


def transcribe_audio(user_input: str):
    """
    Simulated STT for Week 1.
    We pass text instead of real audio.
    """

    if not user_input or user_input.strip() == "":
        return NO_INPUT

    if len(user_input.strip()) < 3:
        return LOW_CONFIDENCE_STT

    return {
        "text": user_input.strip(),
        "confidence": 0.85,
    }
