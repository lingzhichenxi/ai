from seed_rec_agent.agent import RecommendationAgent
from seed_rec_agent.retrieval import HybridRetriever
from seed_rec_agent.sample_data import sample_catalog


agent = RecommendationAgent(HybridRetriever(sample_catalog()))
for query in ("我喜欢历史和悬疑，想看国风", "不要悬疑了，换点新鲜的"):
    response = agent.chat("demo-user", "demo-session", query, 3)
    print(f"\n用户：{query}\nAgent：{response.message}")
    for rec in response.recommendations:
        print(f"- {rec.title} ({rec.score:.3f})：{rec.reason}")

