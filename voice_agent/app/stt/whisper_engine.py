import os
import whisper
import tempfile
import shutil
from app.core.errors_catalog import STT_ENGINE_FAILURE

model = whisper.load_model("small")


def transcribe_audio(uploaded_file):
    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_audio:
            shutil.copyfileobj(uploaded_file.file, temp_audio)
            temp_path = temp_audio.name

        # reset pointer just in case
        uploaded_file.file.seek(0)

        result = model.transcribe(temp_path)

        text = result["text"].strip()

        return {
            "text": text,
            "confidence": 0.9
        }

    except Exception as e:
        print("STT ERROR:", e)
        return STT_ENGINE_FAILURE

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)