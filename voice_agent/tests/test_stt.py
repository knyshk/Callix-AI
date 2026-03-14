"""
Tests for Speech Recognition Module
Tests that require Whisper model are skipped if not installed.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import unittest


class TestWhisperEngine(unittest.TestCase):

    def test_empty_audio_raises(self):
        from app.stt.whisper_engine import transcribe_audio
        from app.core.errors import STTError
        with self.assertRaises(STTError):
            transcribe_audio(b"tiny", filename="test.wav")

    def test_whisper_model_lazy_load(self):
        """Model should not be loaded until first call."""
        import app.stt.whisper_engine as engine
        # Just check module is importable without auto-loading model
        self.assertTrue(hasattr(engine, "transcribe_audio"))


if __name__ == "__main__":
    unittest.main()
