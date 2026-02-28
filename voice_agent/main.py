# # main.py

# from fastapi import FastAPI
# from pydantic import BaseModel
# from app.core.pipeline import run_pipeline


# app = FastAPI()


# class ConversationRequest(BaseModel):
#     text: str


# @app.post("/conversation")
# async def conversation(request: ConversationRequest):
#     result = run_pipeline(request.text)
#     return result






# main.py

import uvicorn

if __name__ == "__main__":
    uvicorn.run("app.api.server:app", host="0.0.0.0", port=8000, reload=True)