# app/core/errors.py

from enum import Enum
from typing import Optional


class ErrorType(str, Enum):
    SYSTEM = "system"
    USER_INPUT = "user_input"
    LOGIC = "logic"


class VoiceError:
    def __init__(
        self,
        code: str,
        message: str,
        error_type: ErrorType,
        recoverable: bool,
        retry_after: Optional[int] = None,
    ):
        self.code = code
        self.message = message
        self.error_type = error_type
        self.recoverable = recoverable
        self.retry_after = retry_after

    def to_dict(self) -> dict:
        return {
            "code": self.code,
            "message": self.message,
            "error_type": self.error_type.value,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after,
        }
