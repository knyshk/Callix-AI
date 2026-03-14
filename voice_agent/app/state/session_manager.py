"""
Session Manager
Tracks active conversation sessions across multiple turns.
Each session holds: conversation_id, FSM instance, turn history, slots, metadata.
"""
import uuid
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.dialogue.fsm import DialogueFSM
from app.core.logger import logger


@dataclass
class ConversationTurn:
    turn_number: int
    user_text: str
    intent: str
    confidence: float
    fsm_state: str
    response_text: str
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class Session:
    session_id: str
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    fsm: DialogueFSM = field(default_factory=DialogueFSM)
    turns: list = field(default_factory=list)
    slots: dict = field(default_factory=dict)   # e.g. {"order_id": "ORD123"}
    pending_intent: Optional[str] = None         # intent being resolved (slot collection)
    config_profile: str = "default"
    caller_id: Optional[str] = None             # for telephony integration
    metadata: dict = field(default_factory=dict)

    @property
    def turn_count(self) -> int:
        return len(self.turns)

    def add_turn(self, user_text: str, intent: str, confidence: float,
                 fsm_state: str, response_text: str):
        turn = ConversationTurn(
            turn_number=self.turn_count + 1,
            user_text=user_text,
            intent=intent,
            confidence=confidence,
            fsm_state=fsm_state,
            response_text=response_text,
        )
        self.turns.append(turn)

    def get_recent_intents(self, n: int = 3) -> list:
        return [t.intent for t in self.turns[-n:]]

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "turn_count": self.turn_count,
            "current_fsm_state": self.fsm.current_state,
            "slots": self.slots,
            "pending_intent": self.pending_intent,
            "caller_id": self.caller_id,
        }


class SessionManager:
    """
    In-memory session store. Manages creation, retrieval, and cleanup of sessions.
    For production, swap _sessions dict with Redis or a database backend.
    """

    def __init__(self):
        self._sessions: Dict[str, Session] = {}

    def create_session(self, caller_id: Optional[str] = None,
                       config_profile: str = "default") -> Session:
        session_id = str(uuid.uuid4())
        session = Session(
            session_id=session_id,
            fsm=DialogueFSM(config_profile),
            config_profile=config_profile,
            caller_id=caller_id,
        )
        self._sessions[session_id] = session
        logger.info("SESSION_CREATED", session_id=session_id, caller_id=caller_id)
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        return self._sessions.get(session_id)

    def get_or_create(self, session_id: Optional[str],
                      caller_id: Optional[str] = None,
                      config_profile: str = "default") -> Session:
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create_session(caller_id=caller_id, config_profile=config_profile)

    def end_session(self, session_id: str):
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info("SESSION_ENDED", session_id=session_id)

    def active_count(self) -> int:
        return len(self._sessions)


# Singleton session manager
session_manager = SessionManager()
