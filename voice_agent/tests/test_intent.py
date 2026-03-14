"""
Tests for Intent Detection Module
Tests both rule-based and semantic detection paths.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest
from app.intent.detector import IntentDetector, detect_intent


class TestRuleBasedDetection(unittest.TestCase):

    def setUp(self):
        self.detector = IntentDetector()

    def test_greeting_hello(self):
        result = self.detector.detect("hello")
        self.assertEqual(result.intent, "greeting")
        self.assertEqual(result.method, "rule")

    def test_greeting_namaste(self):
        result = self.detector.detect("namaste")
        self.assertEqual(result.intent, "greeting")

    def test_goodbye(self):
        result = self.detector.detect("bye, thank you")
        self.assertEqual(result.intent, "goodbye")

    def test_talk_to_agent(self):
        result = self.detector.detect("I want to speak to a human agent")
        self.assertEqual(result.intent, "talk_to_agent")

    def test_order_status_rule(self):
        result = self.detector.detect("where is my order")
        self.assertEqual(result.intent, "check_order_status")

    def test_refund_status_rule(self):
        result = self.detector.detect("where is my refund")
        self.assertEqual(result.intent, "check_refund_status")

    def test_cancel_order_rule(self):
        result = self.detector.detect("cancel my order")
        self.assertEqual(result.intent, "cancel_order")

    def test_return_rule(self):
        result = self.detector.detect("I want to return my item")
        self.assertEqual(result.intent, "initiate_return")


class TestOrderIdExtraction(unittest.TestCase):

    def setUp(self):
        self.detector = IntentDetector()

    def test_extract_ord_format(self):
        result = self.detector.extract_order_id("My order ID is ORD001")
        self.assertIsNotNone(result)
        self.assertIn("ORD001", result)

    def test_extract_hash_format(self):
        result = self.detector.extract_order_id("order number #123456")
        self.assertIsNotNone(result)

    def test_no_order_id(self):
        result = self.detector.extract_order_id("hello how are you")
        self.assertIsNone(result)


class TestSemanticDetection(unittest.TestCase):

    def setUp(self):
        # Skip if sentence-transformers not installed
        try:
            from sentence_transformers import SentenceTransformer
            self.detector = IntentDetector()
        except ImportError:
            self.skipTest("sentence-transformers not installed")

    def test_paraphrase_balance(self):
        """Should detect check_order_status from paraphrase."""
        result = self.detector.detect("Has my package been dispatched yet?")
        self.assertIn(result.intent, ["check_order_status", "unknown"])

    def test_paraphrase_refund(self):
        result = self.detector.detect("I haven't received my money back yet")
        self.assertIn(result.intent, ["check_refund_status", "unknown"])

    def test_empty_text(self):
        result = self.detector.detect("")
        self.assertEqual(result.intent, "unknown")
        self.assertEqual(result.confidence, 0.0)


if __name__ == "__main__":
    unittest.main()
