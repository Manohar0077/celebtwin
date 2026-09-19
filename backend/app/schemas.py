"""Pydantic schemas for API request/response."""
from pydantic import BaseModel, Field
from typing import Optional


class CelebrityMatch(BaseModel):
    name: str
    category: str
    score: float = Field(..., ge=0.0, le=1.0, description="Cosine similarity score 0–1")
    image: Optional[str] = None   # relative path served by /celebrity-images/


class MatchResponse(BaseModel):
    matches: list[CelebrityMatch]
    llm_comment: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    celebrities_loaded: int
