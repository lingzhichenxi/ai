from __future__ import annotations

import time
from dataclasses import asdict

try:
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover
    raise RuntimeError("请先安装 API 依赖：pip install -e '.[api]'") from exc

from .agent import RecommendationAgent
from .models import Behavior, FeedbackType
from .retrieval import HybridRetriever
from .sample_data import sample_catalog

app = FastAPI(title="Seed Recommendation Agent", version="0.1.0")
agent = RecommendationAgent(HybridRetriever(sample_catalog()))


class ChatRequest(BaseModel):
    user_id: str
    session_id: str
    message: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=5, ge=1, le=20)


class FeedbackRequest(BaseModel):
    user_id: str
    item_id: str
    event: FeedbackType
    dwell_seconds: float = Field(default=0, ge=0, le=86400)
    tags: list[str] = []
    timestamp: float | None = None


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/recommend/chat")
def chat(req: ChatRequest):
    return asdict(agent.chat(req.user_id, req.session_id, req.message, req.limit))


@app.post("/v1/recommend/feedback")
def feedback(req: FeedbackRequest):
    if req.item_id not in {x.item_id for x in agent.retriever.catalog}:
        raise HTTPException(404, "item not found")
    agent.feedback(req.user_id, Behavior(
        item_id=req.item_id,
        event=req.event,
        timestamp=req.timestamp or time.time(),
        dwell_seconds=req.dwell_seconds,
        tags=set(req.tags),
    ))
    return {"status": "accepted"}

