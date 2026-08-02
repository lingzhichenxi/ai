from __future__ import annotations

from typing import Protocol

from .models import Candidate, Intent


class SeedModel(Protocol):
    def explain(self, candidate: Candidate, intent: Intent) -> str: ...


class LocalSeedAdapter:
    """Offline deterministic stand-in for the Seed service."""

    def explain(self, candidate: Candidate, intent: Intent) -> str:
        item = candidate.item
        matches = sorted(item.tags & intent.positive_tags)
        if matches:
            return f"符合你对{'、'.join(matches)}的当前需求"
        if "style_match" in candidate.reason_codes:
            return f"匹配你偏好的{'、'.join(sorted(item.style))}画风"
        if "long_tail_exploration" in candidate.reason_codes:
            return "这是一个质量不错、曝光较少的新鲜内容"
        return "综合你的近期兴趣与内容质量推荐"

