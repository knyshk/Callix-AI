"""
Whisper STT Engine
Converts audio input to text using OpenAI Whisper (base model).
Handles audio decoding via FFmpeg and returns structured transcription output.
"""
import os
import uuid
import tempfile
from typing import Optional

from app.core.errors import STTError
from app.core.errors_catalog import ErrorCode
from app.core.logger import logger


# Lazy-load Whisper to avoid heavy import at module level
_whisper_model = None


def _get_model():
    global _whisper_model
    if _whisper_model is None:
        try:
            import whisper
            logger.info("STT_MODEL_LOADING", model="base")
            _whisper_model = whisper.load_model("base")
            logger.info("STT_MODEL_LOADED", model="base")
        except Exception as e:
            raise STTError(ErrorCode.STT_ENGINE_FAILURE, detail=str(e))
    return _whisper_model


def transcribe_audio(audio_bytes: bytes, filename: str = "audio.wav") -> dict:
    """
    Transcribe audio bytes using Whisper.

    Args:
        audio_bytes: Raw audio file bytes
        filename: Original filename (used for extension detection)

    Returns:
        dict with keys: text (str), language (str), confidence (float)
    """
    if not audio_bytes or len(audio_bytes) < 1000:
        raise STTError(ErrorCode.AUDIO_TOO_SHORT)

    # Write audio to a temp file (Whisper requires a file path)
    ext = os.path.splitext(filename)[-1] or ".wav"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        model = _get_model()
        result = model.transcribe(tmp_path, fp16=False)

        text = result.get("text", "").strip()
        language = result.get("language", "en")

        # Whisper doesn't give a confidence score directly; use segment avg log_prob
        segments = result.get("segments", [])
        if segments:
            avg_logprob = sum(s.get("avg_logprob", -1.0) for s in segments) / len(segments)
            # Convert avg log_prob to rough 0-1 confidence
            confidence = max(0.0, min(1.0, (avg_logprob + 1.0)))
        else:
            confidence = 0.9 if text else 0.0

        logger.info("STT_TRANSCRIPTION_DONE", text_preview=text[:50], language=language)
        return {"text": text, "language": language, "confidence": round(confidence, 2)}

    except STTError:
        raise
    except Exception as e:
        logger.error("STT_ENGINE_FAILURE", detail=str(e))
        raise STTError(ErrorCode.STT_ENGINE_FAILURE, detail=str(e))
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except Exception:
                pass
