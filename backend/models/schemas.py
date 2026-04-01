from pydantic import BaseModel
from typing import Optional


class ChatResponse(BaseModel):
    session_id: str
    answer: str


class IngestResponse(BaseModel):
    ingested: int
    chunks: int
    message: str
