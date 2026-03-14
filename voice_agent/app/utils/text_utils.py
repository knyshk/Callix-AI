"""
Text Utilities
Helper functions for text normalization and preprocessing.
"""
import re
import unicodedata


def normalize_text(text: str) -> str:
    """Normalize text: strip whitespace, lowercase, remove special chars."""
    text = text.strip()
    text = unicodedata.normalize("NFKC", text)  # handle unicode variants
    text = re.sub(r"\s+", " ", text)            # collapse whitespace
    return text


def sanitize_for_tts(text: str) -> str:
    """Remove characters that TTS engines may not handle well."""
    text = re.sub(r"[<>{}|\\^`]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate text to max_len characters."""
    return text[:max_len] + "..." if len(text) > max_len else text
