# app/core/errors_catalog.py

from app.core.errors import VoiceError, ErrorType


NO_INPUT = VoiceError(
    code="NO_INPUT",
    message="I could not hear you clearly. Please speak again.",
    error_type=ErrorType.USER_INPUT,
    recoverable=True,
    retry_after=1,
)

LOW_CONFIDENCE_STT = VoiceError(
    code="LOW_CONFIDENCE_STT",
    message="The audio was unclear. Please repeat.",
    error_type=ErrorType.USER_INPUT,
    recoverable=True,
    retry_after=1,
)

UNKNOWN_INTENT = VoiceError(
    code="UNKNOWN_INTENT",
    message="I did not understand your request.",
    error_type=ErrorType.LOGIC,
    recoverable=True,
)

STT_ENGINE_FAILURE = VoiceError(
    code="STT_ENGINE_FAILURE",
    message="There is a system issue. Please try later.",
    error_type=ErrorType.SYSTEM,
    recoverable=False,
)
