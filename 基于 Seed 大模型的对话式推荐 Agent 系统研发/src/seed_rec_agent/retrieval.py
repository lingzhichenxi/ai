from __future__ import annotations

import math

from .models import Candidate, Item, UserProfile


class HybridRetriever:
    """Merges legacy recall, semantic recall and low-exposure exploration."""

    def __init__(self, catalog: list[Item]):
        self.catalog = catalog

    def recall(self, profile: UserProfile, query_tags: set[str], limit: int = 100) -> list[Candidate]:
        candidates: list[Candidate] = []
        wanted = set(query_tags) | {k for k, v in profile.interests.items() if v > 0}
        for item in self.catalog:
            overlap = len(item.tags & wanted) / max(1, len(item.tags | wanted))
            legacy = 0.55 * item.popularity + 0.45 * item.quality
            semantic = overlap
            long_tail = 1.0 / math.sqrt(1.0 + item.exposure_count)
            if semantic > 0 or legacy > 0.25 or profile.is_new:
                candidates.append(Candidate(item=item, source_scores={
                    "legacy": legacy, "semantic": semantic, "long_tail": long_tail,
                }))
        candidates.sort(key=lambda c: max(c.source_scores.values()), reverse=True)
        return candidates[:limit]

