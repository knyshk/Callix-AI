"""
Tests for Conversational Pipeline (text mode)
Does not require audio/Whisper — uses text_input bypass.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from app.core.pipeline import run_pipeline


class TestPipelineTextMode(unittest.TestCase):

    def test_greeting_creates_session(self):
        result = run_pipeline(text_input="hello")
        self.assertIsNotNone(result.session_id)
        self.assertIsNotNone(result.response_text)
        self.assertEqual(result.intent, "greeting")

    def test_order_status_flow(self):
        # First turn: state intent
        r1 = run_pipeline(text_input="I want to check my order status")
        self.assertEqual(r1.intent, "check_order_status")
        self.assertIsNotNone(r1.session_id)

        # Second turn: provide order ID
        r2 = run_pipeline(text_input="my order is ORD001", session_id=r1.session_id)
        self.assertIsNotNone(r2.response_text)
        self.assertNotIn("error", r2.response_text.lower()[:30])

    def test_talk_to_agent_escalates(self):
        result = run_pipeline(text_input="connect me to an agent please")
        self.assertIn(result.fsm_state, ("ESCALATE",))

    def test_goodbye_ends_session(self):
        result = run_pipeline(text_input="bye, thank you")
        self.assertEqual(result.fsm_state, "END")

    def test_unknown_input_clarifies(self):
        result = run_pipeline(text_input="xyzzy frobozz plugh")
        self.assertIn(result.fsm_state, ("CLARIFY", "ESCALATE"))

    def test_multi_turn_session_continuity(self):
        """Same session_id should persist state across turns."""
        r1 = run_pipeline(text_input="check my order status")
        sid = r1.session_id

        r2 = run_pipeline(text_input="ORD002", session_id=sid)
        # Should have progressed past ORDER collection
        self.assertNotEqual(r2.fsm_state, r1.fsm_state)

    def test_no_input_returns_error(self):
        result = run_pipeline()
        self.assertIsNotNone(result.error)

    def test_emotion_frustrated_detected(self):
        result = run_pipeline(text_input="I am so frustrated, I have been waiting for my refund for days")
        self.assertIn(result.emotion, ("frustrated", "neutral"))


class TestBusinessLogic(unittest.TestCase):

    def test_order_found(self):
        from app.business.logic import get_order_status, init_db
        init_db()
        result = get_order_status("ORD001")
        self.assertIsNotNone(result)
        self.assertEqual(result["order_id"], "ORD001")

    def test_order_not_found(self):
        from app.business.logic import get_order_status, init_db
        init_db()
        result = get_order_status("ORD999")
        self.assertIsNone(result)

    def test_refund_status(self):
        from app.business.logic import get_refund_status, init_db
        init_db()
        result = get_refund_status("ORD003")
        self.assertIsNotNone(result)

    def test_cancel_already_shipped(self):
        from app.business.logic import cancel_order, init_db
        init_db()
        result = cancel_order("ORD001")
        self.assertEqual(result["status"], "already_shipped")


if __name__ == "__main__":
    unittest.main()
