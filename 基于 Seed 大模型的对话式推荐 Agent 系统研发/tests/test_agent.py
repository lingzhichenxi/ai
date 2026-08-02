import time

from seed_rec_agent.agent import RecommendationAgent
from seed_rec_agent.intent import InstructionParser
from seed_rec_agent.models import Behavior, FeedbackType
from seed_rec_agent.retrieval import HybridRetriever
from seed_rec_agent.sample_data import sample_catalog


def make_agent():
    return RecommendationAgent(HybridRetriever(sample_catalog()))


def test_parser_understands_positive_negative_and_style():
    intent = InstructionParser().parse("我喜欢历史和悬疑，不要美食，想看国风")
    assert {"历史", "悬疑"} <= intent.positive_tags
    assert "美食" in intent.negative_tags
    assert "国风" in intent.styles


def test_explicit_dislike_filters_related_items():
    agent = make_agent()
    result = agent.chat("u1", "s1", "不要美食，推荐点别的")
    ids = {x.item_id for x in result.recommendations}
    assert "i4" not in ids
    assert "i8" not in ids


def test_style_instruction_changes_top_results():
    agent = make_agent()
    result = agent.chat("u2", "s1", "我喜欢历史，想看国风")
    assert result.recommendations[0].item_id in {"i1", "i5"}
    assert result.recommendations[0].trace["features"]["style_match"] == 1.0


def test_feedback_updates_negative_profile():
    agent = make_agent()
    agent.feedback("u3", Behavior("i6", FeedbackType.DISLIKE, time.time(), tags={"科幻"}))
    result = agent.chat("u3", "s1", "随便看看")
    assert "i3" not in {x.item_id for x in result.recommendations}
    assert "i6" not in {x.item_id for x in result.recommendations}


def test_response_contains_auditable_trace_not_freeform_cot():
    result = make_agent().chat("u4", "s1", "推荐历史内容", 2)
    assert len(result.recommendations) == 2
    assert "features" in result.recommendations[0].trace
    assert "chain_of_thought" not in result.recommendations[0].trace


def test_multi_turn_negative_overrides_previous_interest():
    agent = make_agent()
    agent.chat("u5", "s1", "我喜欢历史和悬疑，想看国风")
    result = agent.chat("u5", "s1", "不要悬疑了，换点新鲜的")
    assert "i1" not in {x.item_id for x in result.recommendations}
