"""
Pipeline Orchestrator
Central module that coordinates all components for a conversation turn.
Flow: STT → Intent Detection → Emotion → FSM Dialogue → Business Logic → Response
"""
import time
from typing import Optional
from dataclasses import dataclass, field

from app.stt.whisper_engine import transcribe_audio
from app.intent.detector import detect_intent, IntentResult
from app.emotion.emotion_detector import detect_emotion
from app.dialogue.fsm import DialogueFSM, DialogueContext, DialogueResponse
from app.state.session_manager import session_manager, Session
from app.business import logic as business_logic
from app.core.logger import logger, Timer
from app.core.errors import CallixError, PipelineError, STTError
from app.core.errors_catalog import ErrorCode


# Intents that need order ID slot filling
SLOT_INTENTS = {"check_order_status", "check_refund_status", "initiate_return", "cancel_order"}


@dataclass
class PipelineResult:
    session_id: str
    response_text: str
    fsm_state: str
    intent: str
    confidence: float
    transcription: Optional[str] = None
    emotion: Optional[str] = None
    audio_response: Optional[bytes] = None
    error: Optional[dict] = None
    metadata: dict = field(default_factory=dict)


def run_pipeline(
    audio_bytes: Optional[bytes] = None,
    text_input: Optional[str] = None,
    session_id: Optional[str] = None,
    caller_id: Optional[str] = None,
    config_profile: str = "default",
    generate_tts: bool = False,
    filename: str = "audio.wav",
) -> PipelineResult:
    """
    Run the full conversational pipeline for one turn.

    Args:
        audio_bytes:    Raw audio bytes (from file upload or telephony)
        text_input:     Direct text input (bypasses STT; for testing)
        session_id:     Existing session ID for multi-turn conversations
        caller_id:      Phone number or caller identifier (telephony)
        config_profile: Organization config profile name
        generate_tts:   Whether to synthesize speech response
        filename:       Original audio filename (for format detection)

    Returns:
        PipelineResult with response text and metadata
    """
    pipeline_start = time.perf_counter()

    # ── Session ────────────────────────────────────────────────────────────
    session = session_manager.get_or_create(
        session_id=session_id,
        caller_id=caller_id,
        config_profile=config_profile,
    )
    logger.log_pipeline_start(session.session_id)

    transcription = None
    intent_result = IntentResult(intent="unknown", confidence=0.0, method="unknown")
    emotion_label = "neutral"

    try:
        # ── Step 1: Speech-to-Text ─────────────────────────────────────────
        if audio_bytes:
            with Timer() as t:
                stt_result = transcribe_audio(audio_bytes, filename=filename)
            transcription = stt_result["text"]
            logger.log_stt(session.session_id, t.elapsed_ms, len(transcription))
        elif text_input:
            transcription = text_input
        else:
            raise PipelineError(ErrorCode.PIPELINE_FAILURE, detail="No audio or text input provided.")

        if not transcription:
            # Empty transcription — treat as unknown intent
            transcription = ""

        # ── Step 2: Intent Detection ────────────────────────────────────────
        with Timer() as t:
            intent_result = detect_intent(transcription, profile=config_profile)
        logger.log_intent(session.session_id, t.elapsed_ms,
                          intent_result.intent, intent_result.confidence)

        # ── Step 3: Emotion Detection ───────────────────────────────────────
        emotion_result = detect_emotion(transcription)
        emotion_label = emotion_result.emotion

        # ── Step 4: Slot Extraction (Order ID) ─────────────────────────────
        order_id = None
        # Check if session already has an order_id slot
        if session.slots.get("order_id"):
            order_id = session.slots["order_id"]
        else:
            # Try to extract from current text
            from app.intent.detector import get_detector
            order_id = get_detector(config_profile).extract_order_id(transcription)
            if order_id:
                session.slots["order_id"] = order_id
                logger.info("SLOT_ORDER_ID_EXTRACTED", order_id=order_id,
                            session_id=session.session_id)

        # Determine effective intent (use pending_intent if we're in slot-collection mode)
        effective_intent = intent_result.intent
        if session.pending_intent and session.fsm.current_state in ("COLLECT_ORDER_ID", "RE_COLLECT_ORDER_ID"):
            effective_intent = session.pending_intent
        elif intent_result.intent in SLOT_INTENTS:
            session.pending_intent = intent_result.intent

        # ── Step 5: Dialogue FSM ────────────────────────────────────────────
        ctx = DialogueContext(
            intent=effective_intent,
            confidence=intent_result.confidence,
            order_id=order_id,
            emotion=emotion_label,
            raw_text=transcription,
        )
        dialogue_response = session.fsm.process(ctx)

        # ── Step 6: Business Logic ──────────────────────────────────────────
        if dialogue_response.action == "execute_business" and order_id:
            bl_result = business_logic.execute_intent(session.pending_intent or effective_intent, order_id)
            ctx.business_result = bl_result

            # Map business result to FSM state
            if bl_result.get("status") == "not_found":
                session.fsm.set_state("NOT_FOUND")
            else:
                session.fsm.set_state("GENERATE_RESPONSE")

            # Re-process FSM with business results
            dialogue_response = session.fsm.process(ctx)

        elif dialogue_response.action == "execute_business" and not order_id:
            # Need order ID — go back to collect
            session.fsm.set_state("COLLECT_ORDER_ID")
            ctx.intent = effective_intent
            ctx.order_id = None
            dialogue_response = session.fsm.process(ctx)

        # ── Step 7: Clean up session if terminal ────────────────────────────
        if dialogue_response.is_terminal or dialogue_response.action == "end":
            session.add_turn(transcription, effective_intent, intent_result.confidence,
                             dialogue_response.state, dialogue_response.message)
            session_manager.end_session(session.session_id)
        else:
            session.add_turn(transcription, effective_intent, intent_result.confidence,
                             dialogue_response.state, dialogue_response.message)

        # ── Step 8: Optional TTS ────────────────────────────────────────────
        audio_response = None
        if generate_tts and dialogue_response.message:
            try:
                from app.tts.tts_engine import synthesize_speech
                audio_response = synthesize_speech(dialogue_response.message)
            except Exception as e:
                logger.warning("TTS_SKIPPED", detail=str(e))

        total_ms = (time.perf_counter() - pipeline_start) * 1000
        logger.log_pipeline_end(session.session_id, total_ms)

        return PipelineResult(
            session_id=session.session_id,
            response_text=dialogue_response.message,
            fsm_state=dialogue_response.state,
            intent=effective_intent,
            confidence=intent_result.confidence,
            transcription=transcription,
            emotion=emotion_label,
            audio_response=audio_response,
            metadata={"turn": session.turn_count, "method": intent_result.method},
        )

    except CallixError as e:
        logger.log_error(e.code.value, e.message, session_id=session.session_id)
        return PipelineResult(
            session_id=session.session_id,
            response_text="I'm having trouble processing your request. Please try again.",
            fsm_state=session.fsm.current_state,
            intent="unknown",
            confidence=0.0,
            transcription=transcription,
            error=e.to_dict(),
        )
    except Exception as e:
        logger.log_error("PIPELINE_FAILURE", str(e), session_id=session.session_id)
        return PipelineResult(
            session_id=session.session_id,
            response_text="An unexpected error occurred. Please try again.",
            fsm_state=session.fsm.current_state,
            intent="unknown",
            confidence=0.0,
            transcription=transcription,
            error={"code": "PIPELINE_FAILURE", "message": str(e)},
        )
