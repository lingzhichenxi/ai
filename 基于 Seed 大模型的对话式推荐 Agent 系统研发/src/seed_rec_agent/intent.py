from __future__ import annotations

import re

from .models import Intent


class InstructionParser:
    """Rule-first parser. A Seed-backed parser can be injected behind the same contract."""

    NEGATION = re.compile(r"(?:不喜欢|不要|别推|少一点|避开|讨厌)\s*([^，。,.!！?？]+)")
    POSITIVE = re.compile(r"(?:喜欢|想看|多来点|推荐|偏好)\s*([^，。,.!！?？]+)")
    STYLE_WORDS = {"国风", "写实", "二次元", "极简", "复古", "赛博朋克", "治愈", "暗黑"}
    STOP = {"的", "内容", "作品", "视频", "一些", "一点", "给我", "关于"}

    def parse(self, text: str) -> Intent:
        normalized = text.strip().lower()
        negative = self._extract(self.NEGATION, normalized)
        positive = self._extract(self.POSITIVE, normalized)
        styles = {word for word in self.STYLE_WORDS if word in normalized}
        # A negated style is a negative constraint, not a preferred style.
        styles -= negative
        return Intent(
            positive_tags=positive - negative - styles,
            negative_tags=negative,
            styles=styles,
            reset=any(x in normalized for x in ("重置偏好", "清空偏好", "重新开始")),
            explore=any(x in normalized for x in ("随便看看", "探索", "换点新鲜", "没看过")),
            explanation=any(x in normalized for x in ("为什么", "解释", "理由")),
        )

    def _extract(self, pattern: re.Pattern[str], text: str) -> set[str]:
        result: set[str] = set()
        for match in pattern.finditer(text):
            phrase = match.group(1)
            for token in re.split(r"[和、与及\s]+", phrase):
                token = token.strip()
                for suffix in ("类型", "题材", "风格"):
                    token = token.removesuffix(suffix)
                token = token.rstrip("了吧呢呀啊嘛")
                if token and token not in self.STOP and len(token) <= 12:
                    result.add(token)
        return result
