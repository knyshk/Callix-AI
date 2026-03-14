"""
Logger Module
Structured logging with latency tracking for all pipeline stages.
Logs: STT_LATENCY_MS, INTENT_LATENCY_MS, PIPELINE_LATENCY_MS
"""
import logging
import json
import time
from datetime import datetime, timezone


class StructuredLogger:
    """Logs events in structured JSON format for easy parsing and monitoring."""

    def __init__(self, name: str = "callix-ai"):
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
        self._logger.setLevel(logging.DEBUG)

    def _emit(self, level: str, event: str, **kwargs):
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event": event,
            **kwargs,
        }
        log_str = json.dumps(record)
        if level == "ERROR":
            self._logger.error(log_str)
        elif level == "WARNING":
            self._logger.warning(log_str)
        elif level == "DEBUG":
            self._logger.debug(log_str)
        else:
            self._logger.info(log_str)

    def info(self, event: str, **kwargs):
        self._emit("INFO", event, **kwargs)

    def error(self, event: str, **kwargs):
        self._emit("ERROR", event, **kwargs)

    def warning(self, event: str, **kwargs):
        self._emit("WARNING", event, **kwargs)

    def debug(self, event: str, **kwargs):
        self._emit("DEBUG", event, **kwargs)

    def log_latency(self, stage: str, latency_ms: float, **kwargs):
        """Log pipeline stage latency."""
        self._emit("INFO", f"{stage}_LATENCY_MS", latency_ms=round(latency_ms, 2), **kwargs)

    def log_pipeline_start(self, session_id: str):
        self._emit("INFO", "PIPELINE_START", session_id=session_id)

    def log_pipeline_end(self, session_id: str, total_ms: float):
        self._emit("INFO", "PIPELINE_LATENCY_MS", session_id=session_id, latency_ms=round(total_ms, 2))

    def log_stt(self, session_id: str, latency_ms: float, text_length: int):
        self._emit("INFO", "STT_LATENCY_MS", session_id=session_id, latency_ms=round(latency_ms, 2), text_length=text_length)

    def log_intent(self, session_id: str, latency_ms: float, intent: str, confidence: float):
        self._emit("INFO", "INTENT_LATENCY_MS", session_id=session_id, latency_ms=round(latency_ms, 2), intent=intent, confidence=round(confidence, 4))

    def log_error(self, code: str, message: str, session_id: str = None, **kwargs):
        self._emit("ERROR", "ERROR_EVENT", code=code, message=message, session_id=session_id, **kwargs)


class Timer:
    """Context manager for measuring execution time in milliseconds."""

    def __init__(self):
        self.elapsed_ms: float = 0.0

    def __enter__(self):
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.elapsed_ms = (time.perf_counter() - self._start) * 1000


# Singleton logger instance
logger = StructuredLogger("callix-ai")
