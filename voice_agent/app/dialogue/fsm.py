"""
Dialogue FSM (Finite State Machine)
Controls multi-turn conversation flow based on detected intents and slot data.
Reads state transition rules from fsm.json config.
Prevents infinite loops via retry tracking.
"""
from typing import Optional
from dataclasses import dataclass, field

from app.core.config_loader import load_fsm_config, load_prompts_config
from app.core.errors import DialogueError
from app.core.errors_catalog import ErrorCode
from app.core.logger import logger


@dataclass
class DialogueContext:
    """Holds runtime context for a single conversation turn."""
    intent: str
    confidence: float
    order_id: Optional[str] = None
    business_result: Optional[dict] = None
    emotion: Optional[str] = None
    raw_text: str = ""


@dataclass
class DialogueResponse:
    state: str
    message: str
    action: Optional[str] = None   # "collect_order_id", "execute_business", "escalate", "end"
    data: dict = field(default_factory=dict)
    needs_order_id: bool = False
    is_terminal: bool = False


class DialogueFSM:
    """
    Finite State Machine for dialogue management.
    Each session has its own FSM instance (managed by SessionManager).
    """

    def __init__(self, config_profile: str = "default"):
        fsm_cfg = load_fsm_config(config_profile)
        self._states = fsm_cfg["states"]
        self._initial = fsm_cfg["initial_state"]
        self._prompts = load_prompts_config(config_profile)["responses"]
        self.current_state: str = self._initial
        self._retry_counts: dict = {}

    def _get_state_cfg(self, state: str) -> dict:
        return self._states.get(state, {})

    def _get_transitions(self, state: str) -> dict:
        return self._get_state_cfg(state).get("transitions", {})

    def _max_retries(self, state: str) -> int:
        return self._get_state_cfg(state).get("max_retries", 2)

    def _transition(self, event: str) -> Optional[str]:
        """Get next state for a given event from current state."""
        transitions = self._get_transitions(self.current_state)
        return transitions.get(event) or transitions.get("unknown")

    def _increment_retry(self, state: str) -> int:
        self._retry_counts[state] = self._retry_counts.get(state, 0) + 1
        return self._retry_counts[state]

    def _prompt(self, key: str, **kwargs) -> str:
        template = self._prompts.get(key, self._prompts.get("CLARIFY", "How can I help you?"))
        try:
            return template.format(**kwargs)
        except KeyError:
            return template

    def process(self, ctx: DialogueContext) -> DialogueResponse:
        """
        Process a dialogue context and determine the next state + response.
        """
        intent = ctx.intent
        logger.debug("FSM_PROCESS", current_state=self.current_state, intent=intent)

        # ── Emotion-aware preamble ───────────────────────────────────────────
        emotion_prefix = ""
        if ctx.emotion in ("frustrated", "angry"):
            emotion_prefix = self._prompts.get(f"emotion_{ctx.emotion}", "") + " "

        # ── Handle slot filling (order ID collection) ──────────────────────
        if self.current_state in ("COLLECT_ORDER_ID", "RE_COLLECT_ORDER_ID"):
            if ctx.order_id:
                # Slot filled — move to business logic execution
                self.current_state = "EXECUTE_BUSINESS_LOGIC"
                return DialogueResponse(
                    state=self.current_state,
                    message="",
                    action="execute_business",
                    needs_order_id=False,
                )
            else:
                # Slot not filled — retry or escalate
                retry_count = self._increment_retry(self.current_state)
                max_r = self._max_retries(self.current_state)
                if retry_count >= max_r:
                    self.current_state = "ESCALATE"
                    msg = emotion_prefix + self._prompt("ESCALATE")
                    return DialogueResponse(state=self.current_state, message=msg,
                                            action="escalate", is_terminal=False)
                self.current_state = "RE_COLLECT_ORDER_ID"
                return DialogueResponse(
                    state=self.current_state,
                    message=emotion_prefix + self._prompt("RE_COLLECT_ORDER_ID"),
                    action="collect_order_id",
                    needs_order_id=True,
                )

        # ── Normal intent-driven transition ───────────────────────────────
        next_state = self._transition(intent)
        if not next_state:
            # No valid transition found; stay and clarify
            next_state = "CLARIFY"

        self.current_state = next_state
        response = self._build_response(next_state, ctx, emotion_prefix)
        return response

    def _build_response(self, state: str, ctx: DialogueContext,
                        emotion_prefix: str = "") -> DialogueResponse:
        """Build the DialogueResponse for the new state."""

        if state == "GREET":
            return DialogueResponse(state=state,
                                    message=emotion_prefix + self._prompt("GREET"))

        if state in ("COLLECT_ORDER_ID",):
            self._retry_counts[state] = 0
            return DialogueResponse(
                state=state,
                message=emotion_prefix + self._prompt("COLLECT_ORDER_ID"),
                action="collect_order_id",
                needs_order_id=True,
            )

        if state == "EXECUTE_BUSINESS_LOGIC":
            return DialogueResponse(state=state, message="",
                                    action="execute_business")

        if state == "GENERATE_RESPONSE":
            # Build response from business result
            msg = self._build_business_message(ctx)
            follow_up = " Is there anything else I can help you with?"
            return DialogueResponse(
                state=state,
                message=emotion_prefix + msg + follow_up,
                data=ctx.business_result or {},
            )

        if state == "NOT_FOUND":
            return DialogueResponse(
                state=state,
                message=emotion_prefix + self._prompt("NOT_FOUND"),
                action="not_found",
            )

        if state == "ESCALATE":
            return DialogueResponse(
                state=state,
                message=emotion_prefix + self._prompt("ESCALATE"),
                action="escalate",
            )

        if state == "END":
            return DialogueResponse(
                state=state,
                message=self._prompt("END"),
                action="end",
                is_terminal=True,
            )

        if state == "CLARIFY":
            retry_count = self._increment_retry("CLARIFY")
            max_r = self._max_retries("CLARIFY")
            if retry_count >= max_r:
                self.current_state = "ESCALATE"
                return DialogueResponse(
                    state="ESCALATE",
                    message=emotion_prefix + self._prompt("ESCALATE"),
                    action="escalate",
                )
            return DialogueResponse(
                state=state,
                message=emotion_prefix + self._prompt("CLARIFY"),
            )

        if state == "HANDLE_INQUIRY":
            return DialogueResponse(
                state=state,
                message=emotion_prefix + self._prompt("HANDLE_INQUIRY"),
            )

        # Fallback
        return DialogueResponse(
            state=state,
            message=emotion_prefix + self._prompt("CLARIFY"),
        )

    def _build_business_message(self, ctx: DialogueContext) -> str:
        """Build human-readable message from business logic result."""
        result = ctx.business_result or {}
        intent = ctx.intent
        order_id = ctx.order_id or ""

        templates = self._prompts
        if intent == "check_order_status":
            status = result.get("status", "processing")
            eta = result.get("eta", "soon")
            t = templates.get("order_status", {}).get(status,
                f"Your order {order_id} status is {status}.")
            return t.format(order_id=order_id, eta=eta)

        if intent == "check_refund_status":
            status = result.get("status", "pending")
            t = templates.get("refund_status", {}).get(status,
                f"Your refund for order {order_id} is {status}.")
            return t.format(order_id=order_id)

        if intent == "initiate_return":
            status = result.get("status", "initiated")
            t = templates.get("return", {}).get(status,
                f"Return request for order {order_id} received.")
            return t.format(order_id=order_id)

        if intent == "cancel_order":
            status = result.get("status", "success")
            t = templates.get("cancel", {}).get(status,
                f"Order {order_id} cancel request received.")
            return t.format(order_id=order_id)

        return result.get("message", f"Your request for order {order_id} has been processed.")

    def set_state(self, state: str):
        """Externally set FSM state (used by pipeline after business logic)."""
        if state in self._states:
            self.current_state = state
        else:
            logger.warning("FSM_INVALID_STATE", state=state)

    def reset(self):
        """Reset FSM to initial state (new conversation)."""
        self.current_state = self._initial
        self._retry_counts = {}
