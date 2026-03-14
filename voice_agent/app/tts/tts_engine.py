"""
TTS Engine
Converts response text to speech audio bytes.
Primary: Coqui TTS (if installed)
Fallback: pyttsx3 (lightweight, cross-platform)
"""
import io
import os
import tempfile
from typing import Optional

from app.core.logger import logger
from app.core.errors import CallixError
from app.core.errors_catalog import ErrorCode


def _try_coqui(text: str) -> Optional[bytes]:
    """Try to use Coqui TTS."""
    try:
        from TTS.api import TTS  # type: ignore
        tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC", progress_bar=False)
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name
        tts.tts_to_file(text=text, file_path=tmp_path)
        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        os.unlink(tmp_path)
        return audio_bytes
    except ImportError:
        return None
    except Exception as e:
        logger.warning("COQUI_TTS_FAILED", detail=str(e))
        return None


def _try_pyttsx3(text: str) -> Optional[bytes]:
    """Use pyttsx3 as fallback TTS engine."""
    try:
        import pyttsx3  # type: ignore
        engine = pyttsx3.init()
        engine.setProperty("rate", 160)
        engine.setProperty("volume", 0.9)

        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name

        engine.save_to_file(text, tmp_path)
        engine.runAndWait()
        engine.stop()

        with open(tmp_path, "rb") as f:
            audio_bytes = f.read()
        os.unlink(tmp_path)
        return audio_bytes
    except Exception as e:
        logger.warning("PYTTSX3_TTS_FAILED", detail=str(e))
        return None


def synthesize_speech(text: str) -> Optional[bytes]:
    """
    Convert text to speech audio bytes.
    Tries Coqui first, falls back to pyttsx3.
    Returns None if both fail (caller should handle gracefully).
    """
    if not text or not text.strip():
        return None

    logger.info("TTS_SYNTHESIZE", text_length=len(text))

    # Try Coqui TTS (higher quality)
    audio = _try_coqui(text)
    if audio:
        logger.info("TTS_SUCCESS", engine="coqui")
        return audio

    # Fallback to pyttsx3
    audio = _try_pyttsx3(text)
    if audio:
        logger.info("TTS_SUCCESS", engine="pyttsx3")
        return audio

    logger.error("TTS_ALL_ENGINES_FAILED")
    return None
