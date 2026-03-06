# app/api/server.py

from fastapi import FastAPI
from pydantic import BaseModel
from app.core.pipeline import run_pipeline

app = FastAPI(title="Voice Agent Backend")


class ConversationRequest(BaseModel):
    brand_id: str
    text: str


class ConversationResponse(BaseModel):
    response: str


@app.post("/conversation", response_model=ConversationResponse)
async def conversation(request: ConversationRequest):
    result = await run_pipeline(request.text, request.brand_id)
    return result