"""
Error Catalog
Defines all structured error codes used across the system.
"""
from enum import Enum


class ErrorCode(str, Enum):
    # STT errors
    STT_ENGINE_FAILURE = "STT_ENGINE_FAILURE"
    AUDIO_PROCESSING_ERROR = "AUDIO_PROCESSING_ERROR"
    AUDIO_TOO_SHORT = "AUDIO_TOO_SHORT"
    UNSUPPORTED_AUDIO_FORMAT = "UNSUPPORTED_AUDIO_FORMAT"

    # Intent errors
    UNKNOWN_INTENT = "UNKNOWN_INTENT"
    INTENT_MODEL_FAILURE = "INTENT_MODEL_FAILURE"

    # Dialogue errors
    FSM_TRANSITION_ERROR = "FSM_TRANSITION_ERROR"
    MAX_RETRIES_EXCEEDED = "MAX_RETRIES_EXCEEDED"

    # Business logic errors
    ORDER_NOT_FOUND = "ORDER_NOT_FOUND"
    BUSINESS_LOGIC_ERROR = "BUSINESS_LOGIC_ERROR"

    # Pipeline errors
    PIPELINE_FAILURE = "PIPELINE_FAILURE"
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"

    # TTS errors
    TTS_ENGINE_FAILURE = "TTS_ENGINE_FAILURE"


ERROR_MESSAGES = {
    ErrorCode.STT_ENGINE_FAILURE: "Speech recognition failed. Please try again.",
    ErrorCode.AUDIO_PROCESSING_ERROR: "There was a problem processing the audio file.",
    ErrorCode.AUDIO_TOO_SHORT: "The audio is too short to process.",
    ErrorCode.UNSUPPORTED_AUDIO_FORMAT: "The audio format is not supported.",
    ErrorCode.UNKNOWN_INTENT: "The system could not understand the request.",
    ErrorCode.INTENT_MODEL_FAILURE: "Intent detection model failed to respond.",
    ErrorCode.FSM_TRANSITION_ERROR: "The conversation flow encountered an error.",
    ErrorCode.MAX_RETRIES_EXCEEDED: "Maximum retry attempts exceeded.",
    ErrorCode.ORDER_NOT_FOUND: "No order was found with the provided ID.",
    ErrorCode.BUSINESS_LOGIC_ERROR: "An error occurred while processing your request.",
    ErrorCode.PIPELINE_FAILURE: "The processing pipeline encountered an unexpected error.",
    ErrorCode.SESSION_NOT_FOUND: "The conversation session was not found.",
    ErrorCode.TTS_ENGINE_FAILURE: "Text-to-speech conversion failed.",
}
