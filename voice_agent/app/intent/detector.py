"""
Intent Detector
Hybrid intent detection using:
  1. Rule-based keyword matching (fast, deterministic, high precision)
  2. Semantic cosine similarity with sentence embeddings (handles paraphrasing)
  3. Optional LLM fallback for ambiguous low-confidence inputs

Returns: IntentResult with intent name and confidence score.
"""
import re
import numpy as np
from typing import Optional
from dataclasses import dataclass

from app.intent.embedding_model import get_embedding, get_embeddings_batch, cosine_similarity
from app.core.config_loader import load_intents_config
from app.core.errors import IntentError
from app.core.errors_catalog import ErrorCode
from app.core.logger import logger


@dataclass
class IntentResult:
    intent: str
    confidence: float
    method: str  # "rule", "semantic", "llm_fallback", "unknown"


# ---------------------------------------------------------------------------
# Rule-based patterns (quick override for very clear phrases)
# ---------------------------------------------------------------------------
RULE_PATTERNS = {
    "greeting": [
        r"\b(hello|hi|hey|namaste|good morning|good evening|good afternoon)\b"
    ],
    "goodbye": [
        r"\b(bye|goodbye|that'?s? all|i'?m done|thank you bye|nothing else|ok thanks)\b"
    ],
    "talk_to_agent": [
        r"\b(human|agent|operator|representative|real person|customer care|transfer|escalate|speak to someone)\b"
    ],
    "check_order_status": [
        r"\b(order status|track.*order|where.*order|order.*arriv|shipment|delivery status|shipping update)\b"
    ],
    "check_refund_status": [
        r"\b(refund status|where.*refund|money back|refund.*time|refund.*process)\b"
    ],
    "initiate_return": [
        r"\b(return.*item|return.*product|want to return|send.*back|return request|initiate.*return)\b"
    ],
    "cancel_order": [
        r"\b(cancel.*order|cancel.*purchase|stop.*order|abort.*order)\b"
    ],
}


class IntentDetector:
    """
    Detects intent from transcribed user text using a hybrid approach.
    """

    def __init__(self, config_profile: str = "default"):
        self._config = load_intents_config(config_profile)
        self._threshold = self._config.get("fallback_threshold", 0.45)
        self._unknown = self._config.get("unknown_intent", "unknown")
        self._intent_embeddings: Optional[dict] = None  # lazy-loaded
        self._intent_names: list = []

    def _load_embeddings(self):
        """Pre-compute embeddings for all intent examples (lazy-loaded once)."""
        if self._intent_embeddings is not None:
            return

        self._intent_embeddings = {}
        intents = self._config.get("intents", [])
        for intent_def in intents:
            name = intent_def["name"]
            examples = intent_def.get("examples", [])
            if examples:
                embeddings = get_embeddings_batch(examples)
                self._intent_embeddings[name] = embeddings
                self._intent_names.append(name)
        logger.info("INTENT_EMBEDDINGS_LOADED", count=len(self._intent_names))

    def _rule_match(self, text: str) -> Optional[IntentResult]:
        """Try to match using rule patterns first (fast path)."""
        lower = text.lower().strip()
        for intent, patterns in RULE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, lower):
                    return IntentResult(intent=intent, confidence=0.95, method="rule")
        return None

    def _semantic_match(self, text: str) -> IntentResult:
        """Use semantic embeddings to find the best intent."""
        self._load_embeddings()

        query_vec = get_embedding(text)
        best_intent = self._unknown
        best_score = 0.0

        for intent_name, example_embeddings in self._intent_embeddings.items():
            # Compute similarity against all examples; take the max
            scores = [cosine_similarity(query_vec, ex_vec) for ex_vec in example_embeddings]
            top_score = max(scores)
            if top_score > best_score:
                best_score = top_score
                best_intent = intent_name

        if best_score >= self._threshold:
            return IntentResult(intent=best_intent, confidence=best_score, method="semantic")
        else:
            return IntentResult(intent=self._unknown, confidence=best_score, method="unknown")

    def detect(self, text: str) -> IntentResult:
        """
        Main detection entry point.
        Pipeline: rule-based → semantic → unknown
        """
        if not text or not text.strip():
            return IntentResult(intent=self._unknown, confidence=0.0, method="unknown")

        # Step 1: Rule-based fast path
        rule_result = self._rule_match(text)
        if rule_result:
            logger.debug("INTENT_RULE_MATCH", intent=rule_result.intent, text=text[:60])
            return rule_result

        # Step 2: Semantic similarity
        try:
            semantic_result = self._semantic_match(text)
            logger.debug("INTENT_SEMANTIC", intent=semantic_result.intent,
                         confidence=semantic_result.confidence, text=text[:60])
            return semantic_result
        except Exception as e:
            logger.error("INTENT_SEMANTIC_FAILURE", detail=str(e))
            return IntentResult(intent=self._unknown, confidence=0.0, method="unknown")

    def extract_order_id(self, text: str) -> Optional[str]:
        """
        Extract order ID from user text.
        Supports formats like: ORD123, ORD-456, #789, order number 123
        """
        patterns = [
            r"\b(ORD[-\s]?\d{3,10})\b",          # ORD123, ORD-456
            r"\border\s*(?:id|number|#)?\s*[:#]?\s*(\w{3,15})\b",  # order id ABC123
            r"#(\d{4,12})\b",                       # #12345
            r"\b(\d{6,12})\b",                      # plain numeric IDs
        ]
        text_upper = text.upper()
        for pattern in patterns:
            match = re.search(pattern, text_upper, re.IGNORECASE)
            if match:
                return match.group(1).replace(" ", "").replace("-", "").upper()
        return None


# Singleton detector instance
_detector_instance: Optional[IntentDetector] = None


def get_detector(profile: str = "default") -> IntentDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = IntentDetector(profile)
    return _detector_instance


def detect_intent(text: str, profile: str = "default") -> IntentResult:
    """Convenience function to detect intent from text."""
    return get_detector(profile).detect(text)
