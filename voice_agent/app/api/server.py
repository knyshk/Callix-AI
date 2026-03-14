"""
FastAPI Server
Exposes the conversational pipeline via REST API.
Endpoints:
  POST /conversation     — audio file upload (main endpoint)
  POST /conversation/text — text-based input (for testing)
  POST /voice            — telephony webhook (Twilio/Plivo compatible)
  GET  /session/{id}     — get session info
  DELETE /session/{id}   — end session
  GET  /health           — health check
"""
import base64
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.core.pipeline import run_pipeline
from app.state.session_manager import session_manager
from app.core.logger import logger
from app.business.logic import init_db


# ── App initialization ─────────────────────────────────────────────────────
app = FastAPI(
    title="Callix-AI",
    description="Intelligent Conversational Voice Agent for Customer Care Automation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize database and warm up models on startup."""
    logger.info("SERVER_STARTING")
    init_db()
    logger.info("WHISPER_PRELOADING")
    from app.stt.whisper_engine import _get_model
    _get_model()
    logger.info("WHISPER_READY")
    logger.info("SERVER_READY")

# ── Request / Response Models ──────────────────────────────────────────────

class TextConversationRequest(BaseModel):
    text: str
    session_id: Optional[str] = None
    caller_id: Optional[str] = None
    config_profile: str = "default"
    generate_tts: bool = False


class ConversationResponse(BaseModel):
    session_id: str
    response_text: str
    fsm_state: str
    intent: str
    confidence: float
    transcription: Optional[str] = None
    emotion: Optional[str] = None
    audio_base64: Optional[str] = None
    error: Optional[dict] = None
    metadata: dict = {}


# ── Endpoints ──────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "active_sessions": session_manager.active_count(),
        "service": "callix-ai",
    }


@app.post("/conversation", response_model=ConversationResponse)
async def conversation_audio(
    audio: UploadFile = File(..., description="Audio file (wav, mp3, ogg, etc.)"),
    session_id: Optional[str] = Form(None),
    caller_id: Optional[str] = Form(None),
    config_profile: str = Form("default"),
    generate_tts: bool = Form(False),
):
    """
    Main conversation endpoint.
    Accepts audio file + optional session/caller metadata.
    Returns text response + optional synthesized audio.
    """
    audio_bytes = await audio.read()
    result = run_pipeline(
        audio_bytes=audio_bytes,
        session_id=session_id,
        caller_id=caller_id,
        config_profile=config_profile,
        generate_tts=generate_tts,
        filename=audio.filename or "audio.wav",
    )

    audio_b64 = None
    if result.audio_response:
        audio_b64 = base64.b64encode(result.audio_response).decode("utf-8")

    return ConversationResponse(
        session_id=result.session_id,
        response_text=result.response_text,
        fsm_state=result.fsm_state,
        intent=result.intent,
        confidence=result.confidence,
        transcription=result.transcription,
        emotion=result.emotion,
        audio_base64=audio_b64,
        error=result.error,
        metadata=result.metadata,
    )


@app.post("/conversation/text", response_model=ConversationResponse)
async def conversation_text(request: TextConversationRequest):
    """
    Text-based conversation endpoint (bypasses STT).
    Useful for development, testing, and chat interfaces.
    """
    result = run_pipeline(
        text_input=request.text,
        session_id=request.session_id,
        caller_id=request.caller_id,
        config_profile=request.config_profile,
        generate_tts=request.generate_tts,
    )

    audio_b64 = None
    if result.audio_response:
        audio_b64 = base64.b64encode(result.audio_response).decode("utf-8")

    return ConversationResponse(
        session_id=result.session_id,
        response_text=result.response_text,
        fsm_state=result.fsm_state,
        intent=result.intent,
        confidence=result.confidence,
        transcription=result.transcription,
        emotion=result.emotion,
        audio_base64=audio_b64,
        error=result.error,
        metadata=result.metadata,
    )


@app.post("/voice")
async def telephony_webhook(request: Request):
    """
    Telephony webhook endpoint compatible with Twilio and Plivo.
    
    Twilio sends audio via RecordingUrl or streams.
    Plivo sends audio via recording_url.
    
    For Twilio TwiML responses, this returns XML.
    For Plivo, this returns JSON with speak action.
    
    Currently returns a simple TwiML-compatible response for testing.
    Integrate your Twilio/Plivo account to activate real call handling.
    """
    form_data = await request.form()
    
    # Detect provider
    caller_id = str(form_data.get("From") or form_data.get("From") or "unknown")
    call_sid = str(form_data.get("CallSid") or form_data.get("CallUUID") or "unknown")
    speech_result = str(form_data.get("SpeechResult") or "")
    recording_url = str(form_data.get("RecordingUrl") or "")

    session_id = form_data.get("session_id") or call_sid

    logger.info("TELEPHONY_WEBHOOK", caller_id=caller_id, call_sid=call_sid,
                has_speech=bool(speech_result), has_recording=bool(recording_url))

    response_text = "Hello! Welcome to customer support. How can I help you?"

    if speech_result:
        result = run_pipeline(
            text_input=speech_result,
            session_id=session_id,
            caller_id=caller_id,
        )
        response_text = result.response_text

    elif recording_url:
        # Download audio from telephony provider and process
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                audio_response = await client.get(recording_url)
                audio_bytes = audio_response.content
            result = run_pipeline(
                audio_bytes=audio_bytes,
                session_id=session_id,
                caller_id=caller_id,
                filename="telephony.wav",
            )
            response_text = result.response_text
        except Exception as e:
            logger.error("TELEPHONY_AUDIO_FETCH_FAILED", detail=str(e))

    # Return Twilio-compatible TwiML
    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say voice="Polly.Aditi" language="en-IN">{response_text}</Say>
    <Gather input="speech" action="/voice" method="POST"
            speechTimeout="2" language="en-IN"
            speechModel="phone_call">
    </Gather>
    <Say voice="Polly.Aditi" language="en-IN">I did not catch that. Please try again.</Say>
    <Gather input="speech" action="/voice" method="POST"
            speechTimeout="2" language="en-IN"
            speechModel="phone_call">
    </Gather>
</Response>"""
    return Response(content=twiml, media_type="application/xml")


@app.get("/session/{session_id}")
async def get_session(session_id: str):
    """Get information about an active conversation session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.to_dict()


@app.delete("/session/{session_id}")
async def end_session(session_id: str):
    """Explicitly end a conversation session."""
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session_manager.end_session(session_id)
    return {"status": "ended", "session_id": session_id}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("UNHANDLED_EXCEPTION", detail=str(exc), path=str(request.url))
    return JSONResponse(
        status_code=500,
        content={"code": "INTERNAL_ERROR", "message": "An unexpected server error occurred."},
    )
