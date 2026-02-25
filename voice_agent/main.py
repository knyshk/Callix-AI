# main.py

from fastapi import FastAPI
from pydantic import BaseModel
from app.core.pipeline import run_pipeline


app = FastAPI()


class ConversationRequest(BaseModel):
    text: str


@app.post("/conversation")
async def conversation(request: ConversationRequest):
    result = run_pipeline(request.text)
    return result