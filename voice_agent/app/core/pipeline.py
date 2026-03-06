import time
import asyncio
from app.stt.whisper_engine import transcribe_audio
from app.intent.detector import detect_intent
from app.dialogue.fsm import handle_pipeline
from app.core.errors import VoiceError
from app.core.logger import log_event
from app.core.config_loader import load_brand_config


async def run_pipeline(user_input: str, brand_id: str = "default") -> dict:

    pipeline_start = time.perf_counter()
    brand_config = load_brand_config(brand_id)

    loop = asyncio.get_running_loop()

    # ---- STT (CPU offloaded) ----
    stt_start = time.perf_counter()
    stt_result = await loop.run_in_executor(None, transcribe_audio, user_input)
    stt_latency = (time.perf_counter() - stt_start) * 1000
    log_event("STT_LATENCY_MS", {"latency": round(stt_latency, 2)})

    if isinstance(stt_result, VoiceError):
        log_event("STT_ERROR", {"code": stt_result.code})
        return handle_pipeline(stt_result, None)

    # ---- INTENT ----
    intent_start = time.perf_counter()
    intent_result = detect_intent(stt_result["text"])
    intent_latency = (time.perf_counter() - intent_start) * 1000
    log_event("INTENT_LATENCY_MS", {"latency": round(intent_latency, 2)})

    if isinstance(intent_result, VoiceError):
        log_event("INTENT_ERROR", {"code": intent_result.code})
    else:
        if intent_result["intent"] not in brand_config["supported_intents"]:
            return {"response": "This service is not available for your brand."}
        log_event("INTENT_SUCCESS", {"intent": intent_result["intent"]})

    total_latency = (time.perf_counter() - pipeline_start) * 1000
    log_event("PIPELINE_LATENCY_MS", {"latency": round(total_latency, 2)})

    return handle_pipeline(stt_result, intent_result)