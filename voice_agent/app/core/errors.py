"""
Error Handling Module
Provides structured error classes and a helper to build standardized error responses.
"""
from typing import Optional
from app.core.errors_catalog import ErrorCode, ERROR_MESSAGES


class CallixError(Exception):
    """Base error class for all Callix-AI errors."""

    def __init__(self, code: ErrorCode, detail: Optional[str] = None):
        self.code = code
        self.message = ERROR_MESSAGES.get(code, "An unexpected error occurred.")
        self.detail = detail
        super().__init__(self.message)

    def to_dict(self) -> dict:
        result = {"code": self.code.value, "message": self.message}
        if self.detail:
            result["detail"] = self.detail
        return result


class STTError(CallixError):
    pass


class IntentError(CallixError):
    pass


class DialogueError(CallixError):
    pass


class BusinessLogicError(CallixError):
    pass


class PipelineError(CallixError):
    pass


def make_error_response(code: ErrorCode, detail: Optional[str] = None) -> dict:
    """Build a standardized error response dict."""
    message = ERROR_MESSAGES.get(code, "An unexpected error occurred.")
    result = {"code": code.value, "message": message}
    if detail:
        result["detail"] = detail
    return result
