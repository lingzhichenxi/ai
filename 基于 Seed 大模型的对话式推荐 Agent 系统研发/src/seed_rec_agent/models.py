from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FeedbackType(str, Enum):
    CLICK = "click"
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"
    EXPOSE = "expose"


@dataclass(slots=True)
class Item:
    item_id: str
    title: str
    description: str
    tags: set[str]
    style: set[str] = field(default_factory=set)
    quality: float = 0.5
    popularity: float = 0.5
    exposure_count: int = 0
    embedding: list[float] = field(default_factory=list)


@dataclass(slots=True)
class Behavior:
    item_id: str
    event: FeedbackType
    timestamp: float
    dwell_seconds: float = 0.0
    tags: set[str] = field(default_factory=set)


@dataclass(slots=True)
class UserProfile:
    user_id: str
    interests: dict[str, float] = field(default_factory=dict)
    disliked_tags: dict[str, float] = field(default_factory=dict)
    preferred_styles: set[str] = field(default_factory=set)
    history: list[Behavior] = field(default_factory=list)
    turn_count: int = 0

    @property
    def is_new(self) -> bool:
        return len(self.history) < 5


@dataclass(slots=True)
class Intent:
    positive_tags: set[str] = field(default_factory=set)
    negative_tags: set[str] = field(default_factory=set)
    styles: set[str] = field(default_factory=set)
    reset: bool = False
    explore: bool = False
    explanation: bool = False


@dataclass(slots=True)
class Candidate:
    item: Item
    source_scores: dict[str, float] = field(default_factory=dict)
    features: dict[str, float] = field(default_factory=dict)
    score: float = 0.0
    reason_codes: list[str] = field(default_factory=list)


@dataclass(slots=True)
class Recommendation:
    item_id: str
    title: str
    score: float
    reason: str
    trace: dict[str, Any]


@dataclass(slots=True)
class AgentResponse:
    session_id: str
    message: str
    recommendations: list[Recommendation]
    parsed_intent: Intent
    request_id: str

