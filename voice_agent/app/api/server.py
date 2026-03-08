from fastapi import FastAPI, UploadFile, File, Form
from app.core.pipeline import run_pipeline

app = FastAPI(title="Voice Agent Backend")


@app.post("/conversation")
async def conversation(
    brand_id: str = Form(...),
    audio: UploadFile = File(...)
):
    result = await run_pipeline(audio, brand_id)
    return result