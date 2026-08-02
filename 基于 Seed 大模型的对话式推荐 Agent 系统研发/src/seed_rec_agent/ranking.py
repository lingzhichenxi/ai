from __future__ import annotations

import hashlib
import math

from .models import Candidate, Intent, UserProfile


class CoTFeatureBuilder:
    """Builds auditable intermediate evidence; private free-form CoT is never exposed."""

    def build(self, candidate: Candidate, profile: UserProfile, intent: Intent) -> dict[str, float]:
        item = candidate.item
        positive = sum(profile.interests.get(t, 0.0) for t in item.tags)
        explicit = len(item.tags & intent.positive_tags)
        dislike = sum(profile.disliked_tags.get(t, 0.0) for t in item.tags)
        explicit_negative = len(item.tags & intent.negative_tags)
        style = len(item.style & profile.preferred_styles) / max(1, len(profile.preferred_styles))
        novelty = candidate.source_scores["long_tail"]
        # Stable pseudo-randomness makes exploration testable and session-independent.
        exploration = int(hashlib.sha1(item.item_id.encode()).hexdigest()[:6], 16) / 0xFFFFFF
        return {
            "interest_match": math.tanh(positive / 3.0),
            "explicit_match": min(1.0, float(explicit)),
            "dislike_risk": min(1.0, dislike / 3.0 + explicit_negative),
            "style_match": style,
            "quality": item.quality,
            "legacy_score": candidate.source_scores["legacy"],
            "semantic_score": candidate.source_scores["semantic"],
            "novelty": novelty,
            "exploration": exploration,
        }


class FusionRanker:
    def rank(self, candidates: list[Candidate], profile: UserProfile, intent: Intent, limit: int) -> list[Candidate]:
        builder = CoTFeatureBuilder()
        for c in candidates:
            f = c.features = builder.build(c, profile, intent)
            explore_weight = 0.18 if profile.is_new or intent.explore else 0.04
            dislike_penalty = 1.8 * f["dislike_risk"]
            c.score = (
                0.24 * f["legacy_score"] + 0.23 * f["semantic_score"]
                + 0.20 * f["interest_match"] + 0.15 * f["explicit_match"]
                + 0.10 * f["style_match"] + 0.08 * f["quality"]
                + explore_weight * (0.65 * f["novelty"] + 0.35 * f["exploration"])
                - dislike_penalty
            )
            if f["dislike_risk"] > 0:
                c.reason_codes.append("negative_constraint")
            if f["explicit_match"] > 0:
                c.reason_codes.append("explicit_request")
            if f["style_match"] > 0:
                c.reason_codes.append("style_match")
            if f["novelty"] > 0.2:
                c.reason_codes.append("long_tail_exploration")
        eligible = [c for c in candidates if c.features["dislike_risk"] < 0.67]
        eligible.sort(key=lambda c: c.score, reverse=True)
        return self._diversify(eligible, limit)

    def _diversify(self, ranked: list[Candidate], limit: int) -> list[Candidate]:
        chosen: list[Candidate] = []
        remaining = ranked[:]
        while remaining and len(chosen) < limit:
            def mmr(c: Candidate) -> float:
                similarity = max((len(c.item.tags & x.item.tags) / max(1, len(c.item.tags | x.item.tags)) for x in chosen), default=0)
                return 0.85 * c.score - 0.15 * similarity
            best = max(remaining, key=mmr)
            chosen.append(best)
            remaining.remove(best)
        return chosen

