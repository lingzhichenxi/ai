from __future__ import annotations

from dataclasses import dataclass

from .models import Behavior, Item, UserProfile


@dataclass(slots=True)
class JointTrainingExample:
    prompt: str
    target: str
    recommendation_tokens: list[str]
    loss_mask: list[int]
    metadata: dict[str, str]


class JointTokenDatasetBuilder:
    """Creates interleaved natural-language/recommendation-token SFT examples.

    `<ITEM_x>` tokens are added as tokenizer special tokens in the real Seed training
    job. The loss mask indicates which whitespace-delimited target units contribute
    to loss and is intentionally framework-neutral.
    """

    def build(self, profile: UserProfile, candidates: list[Item], query: str) -> JointTrainingExample:
        history = " ".join(self._event_token(x) for x in profile.history[-20:]) or "<COLD_START>"
        interests = "、".join(k for k, _ in sorted(profile.interests.items(), key=lambda x: -x[1])[:10]) or "未知"
        candidate_context = "\n".join(
            f"<ITEM_{x.item_id}> 标题={x.title}; 内容={x.description}; 标签={'/'.join(sorted(x.tags))}"
            for x in candidates
        )
        selected = [x for x in candidates if not (x.tags & profile.disliked_tags.keys())][:5]
        rec_tokens = [f"<ITEM_{x.item_id}>" for x in selected]
        rationale = "推荐结果应匹配当前需求，同时规避负反馈并保持一定新颖性。"
        target_units = rec_tokens + [rationale]
        return JointTrainingExample(
            prompt=(f"用户兴趣：{interests}\n历史行为：{history}\n当前请求：{query}\n"
                    f"候选内容：\n{candidate_context}\n请输出推荐 Token 与简短理由。"),
            target=" ".join(target_units),
            recommendation_tokens=rec_tokens,
            loss_mask=[1] * len(target_units),
            metadata={"user_id": profile.user_id, "schema": "joint-rec-text-v1"},
        )

    @staticmethod
    def _event_token(event: Behavior) -> str:
        return f"<{event.event.value.upper()}_{event.item_id}>"


def joint_loss_formula(rec_ce: float, text_ce: float, alignment_loss: float,
                       rec_weight: float = 0.55, text_weight: float = 0.35,
                       alignment_weight: float = 0.10) -> float:
    """Reference objective: item-token CE + language CE + representation alignment."""
    if abs(rec_weight + text_weight + alignment_weight - 1.0) > 1e-6:
        raise ValueError("loss weights must sum to 1")
    return rec_weight * rec_ce + text_weight * text_ce + alignment_weight * alignment_loss

