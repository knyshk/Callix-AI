# Callix-AI 🎙️
**Intelligent Conversational Voice Agent for Customer Care Automation**

A modular, production-ready voice AI backend built with Python + FastAPI. Processes spoken customer queries through a full pipeline: Speech Recognition → Intent Detection → Dialogue Management → Business Logic → Response.

---

## Architecture

```
phone/audio input
      ↓
  API Layer (FastAPI)
      ↓
  Pipeline Orchestrator
      ↓
  ┌───────────────────────────────┐
  │  Whisper STT                  │  audio → text
  │  Hybrid Intent Detector       │  rule-based + semantic embeddings
  │  Emotion Detector             │  frustration / anger signals
  │  FSM Dialogue Manager         │  multi-turn conversation state
  │  Business Logic Layer         │  order/refund/return/cancel (SQLite)
  │  TTS Engine                   │  text → speech (Coqui / pyttsx3)
  └───────────────────────────────┘
      ↓
  JSON + Audio Response
```

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt

# Download spaCy model (optional, for future NLP use)
python -m spacy download en_core_web_sm

# FFmpeg is required for Whisper audio decoding
# Ubuntu/Debian:
sudo apt install ffmpeg
# macOS:
brew install ffmpeg
```

### 2. Run the server
```bash
python main.py
# or
uvicorn app.api.server:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Open Swagger UI
Visit: http://localhost:8000/docs

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/conversation` | Upload audio file for voice conversation |
| POST | `/conversation/text` | Text-based conversation (testing) |
| POST | `/voice` | Telephony webhook (Twilio/Plivo) |
| GET  | `/session/{id}` | Get session info |
| DELETE | `/session/{id}` | End a session |
| GET  | `/health` | Health check |

### Example: Text Conversation
```bash
curl -X POST http://localhost:8000/conversation/text \
  -H "Content-Type: application/json" \
  -d '{"text": "Where is my order?", "session_id": null}'
```

### Example: Audio Upload
```bash
curl -X POST http://localhost:8000/conversation \
  -F "audio=@my_audio.wav" \
  -F "session_id="
```

---

## Multi-Turn Conversation Flow

```
User:   "Hello"
Bot:    "Hi! How can I help you today?"

User:   "I want to check my order status"
Bot:    "Sure! Could you please share your order ID?"

User:   "ORD001"
Bot:    "Your order ORD001 has been shipped and is on its way. Expected delivery: March 12, 2026. Is there anything else?"

User:   "bye"
Bot:    "Thank you for contacting us. Have a great day!"
```

---

## Intent Detection

Uses a **hybrid approach** to avoid rigid hardcoded matching:

1. **Rule-based** (fast path): Regex patterns for clear phrases like "cancel my order", "hello", etc.
2. **Semantic embeddings** (main path): Sentence-Transformers (`all-MiniLM-L6-v2`) + cosine similarity against intent examples
3. **Unknown fallback**: Low-confidence detections fall back to clarification or escalation

---

## Mock Data (E-commerce)

Pre-loaded orders for testing:
| Order ID | Status | Product |
|----------|--------|---------|
| ORD001 | shipped | Bluetooth Headphones |
| ORD002 | processing | Running Shoes |
| ORD003 | delivered | Laptop Stand |
| ORD004 | cancelled | Yoga Mat |
| ORD005 | shipped | Smart Watch |

---

## Telephony Integration (Twilio)

1. Get a Twilio number at https://twilio.com
2. Point the webhook to: `https://your-domain.com/voice`
3. Twilio will POST speech transcriptions or audio URLs
4. The `/voice` endpoint returns TwiML XML responses

For local testing, use [ngrok](https://ngrok.com):
```bash
ngrok http 8000
# Use the HTTPS URL as your Twilio webhook
```

---

## Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_intent.py -v
python -m pytest tests/test_pipeline.py -v
```

---

## Project Structure

```
voice_agent/
├── main.py                          # Entry point
├── requirements.txt
├── configs/default/
│   ├── intents.json                 # Intent definitions + examples
│   ├── fsm.json                     # FSM state transitions
│   └── prompts.json                 # Response templates
├── app/
│   ├── api/server.py                # FastAPI endpoints
│   ├── core/
│   │   ├── pipeline.py              # Central orchestrator
│   │   ├── logger.py                # Structured JSON logger
│   │   ├── errors.py                # Error classes
│   │   ├── errors_catalog.py        # Error code definitions
│   │   └── config_loader.py         # JSON config loader
│   ├── stt/whisper_engine.py        # Whisper STT
│   ├── intent/
│   │   ├── detector.py              # Hybrid intent detector
│   │   └── embedding_model.py       # Sentence-Transformers wrapper
│   ├── dialogue/fsm.py              # Finite State Machine
│   ├── emotion/emotion_detector.py  # Rule-based emotion detection
│   ├── tts/tts_engine.py            # TTS (Coqui / pyttsx3)
│   ├── state/session_manager.py     # Multi-turn session tracking
│   ├── business/logic.py            # Business logic + SQLite
│   └── utils/
│       ├── audio_utils.py
│       └── text_utils.py
└── tests/
    ├── test_intent.py
    ├── test_pipeline.py
    └── test_stt.py
```

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python + FastAPI + Uvicorn |
| STT | OpenAI Whisper (base model) |
| Audio Decoding | FFmpeg |
| Intent Detection | Sentence-Transformers + regex rules |
| Dialogue | Custom FSM (JSON-driven) |
| Emotion Detection | Rule-based keyword analysis |
| TTS | Coqui TTS / pyttsx3 fallback |
| Business Logic | SQLite (via SQLAlchemy) |
| Telephony | Twilio / Plivo webhook compatible |

---

## Prepared by
- Kanishk Jain (2023Btech040)
- Tanveer Kanderiya (2023Btech091)

Faculty Guide: Mr. Santosh Verma  
JKLU — Institute of Engineering and Technology (IET)
