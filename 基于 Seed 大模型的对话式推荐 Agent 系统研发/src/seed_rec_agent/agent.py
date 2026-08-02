from __future__ import annotations

import uuid

from .intent import InstructionParser
from .models import AgentResponse, Behavior, Intent, Recommendation
from .profile import ProfileUpdater
from .ranking import FusionRanker
from .retrieval import HybridRetriever
from .seed_adapter import LocalSeedAdapter, SeedModel
from .store import InMemoryProfileStore


class RecommendationAgent:
    def __init__(self, retriever: HybridRetriever, seed: SeedModel | None = None):
        self.retriever = retriever
        self.seed = seed or LocalSeedAdapter()
        self.parser = InstructionParser()
        self.updater = ProfileUpdater()
        self.ranker = FusionRanker()
        self.store = InMemoryProfileStore()

    def chat(self, user_id: str, session_id: str, message: str, limit: int = 5) -> AgentResponse:
        intent = self.parser.parse(message)
        profile = self.store.get(user_id)
        self.updater.apply_intent(profile, intent)
        candidates = self.retriever.recall(profile, intent.positive_tags)
        ranked = self.ranker.rank(candidates, profile, intent, limit)
        recs = [Recommendation(
            item_id=c.item.item_id,
            title=c.item.title,
            score=round(c.score, 6),
            reason=self.seed.explain(c, intent),
            trace={"reason_codes": c.reason_codes, "features": {k: round(v, 4) for k, v in c.features.items()}},
        ) for c in ranked]
        return AgentResponse(
            session_id=session_id,
            message="已根据你的最新要求调整推荐。" if recs else "暂时没有满足全部条件的内容，可以放宽一个条件再试试。",
            recommendations=recs,
            parsed_intent=intent,
            request_id=str(uuid.uuid4()),
        )

    def feedback(self, user_id: str, behavior: Behavior) -> None:
        self.updater.apply_feedback(self.store.get(user_id), behavior)

