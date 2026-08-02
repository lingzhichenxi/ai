# 基于 Seed 大模型的对话式推荐 Agent

一个可运行的推荐 Agent 工程原型。它把自然语言偏好、历史行为、负反馈和原有推荐分数合并到统一召回/精排链路中，并通过可审计特征而不是暴露自由文本思维链来解释排序。

## 已实现能力

- 正向、负向、画风、探索和偏好重置指令解析
- 行为时间衰减、停留时长加权、重复 Dislike 动态增强
- Legacy、语义和低曝光内容三路召回融合
- 冷启动探索、动态负反馈硬过滤、MMR 多样性重排
- 对话内实时更新画像，返回推荐理由和结构化排序证据
- Seed 模型适配协议及无需密钥即可演示的本地实现
- FastAPI 对话/反馈接口、样例数据和自动化测试
- 联合 Token 训练样本构造器与多任务损失参考实现

## 快速运行

```powershell
python -m venv .venv
.venv\Scripts\pip install -e ".[api,dev]"
.venv\Scripts\python scripts\demo.py
.venv\Scripts\pytest -q
.venv\Scripts\uvicorn seed_rec_agent.api:app --reload
```

接口地址为 `POST /v1/recommend/chat`、`POST /v1/recommend/feedback`，健康检查为 `GET /health`。Swagger 文档默认位于 `http://127.0.0.1:8000/docs`。

## 生产接入点

`SeedModel` 协议用于替换真实 Seed 推理服务；`HybridRetriever` 中的 `legacy` 分数用于承接原有召回/多任务模型；`InMemoryProfileStore` 在生产中应替换为 Redis + 特征存储。在线链路建议增加超时、熔断、批推理、缓存、灰度实验与全链路埋点。

更完整的说明见 [系统架构](docs/ARCHITECTURE.md)。

## 说明

项目中的 CoT 采用“结构化推理特征 + reason code + 最终解释”实现。这样可以训练和调试多步决策，又不会向客户端泄露模型私有自由文本思维链。样例中的模型与指标均用于工程验证，不能冒充线上实验数据。
