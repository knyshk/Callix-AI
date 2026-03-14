"""
Audio Utilities
Helper functions for audio format validation and preprocessing.
"""
import io
from typing import Optional


SUPPORTED_FORMATS = {".wav", ".mp3", ".ogg", ".flac", ".m4a", ".webm", ".mp4"}


def validate_audio_format(filename: str) -> bool:
    """Check if the audio file format is supported."""
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in SUPPORTED_FORMATS


def get_audio_duration_estimate(audio_bytes: bytes) -> float:
    """
    Estimate audio duration in seconds from file size.
    Very rough estimate for WAV (assumes 16kHz mono 16-bit).
    """
    # For WAV: bytes / (sample_rate * channels * bit_depth/8)
    # 16kHz mono 16-bit = 32000 bytes/sec
    estimated_seconds = len(audio_bytes) / 32000
    return round(estimated_seconds, 1)
