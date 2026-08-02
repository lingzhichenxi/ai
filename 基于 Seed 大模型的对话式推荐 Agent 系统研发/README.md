# 基于 Seed 大模型的对话式推荐 Agent 系统研发

这是一个可本地运行的对话式推荐 Agent 原型。项目使用自然语言指令、历史行为和内容特征更新用户画像，再融合传统推荐分数、语义匹配和长尾探索分数完成召回与精排。

当前仓库默认使用 `LocalSeedAdapter` 生成推荐理由，因此**不需要模型密钥即可运行**。项目已经定义 `SeedModel` 适配协议，但没有内置真实 Seed 在线服务、真实业务数据或线上实验结果。

## 项目解决了什么问题？

传统推荐系统主要依赖用户 ID、内容 ID 和历史点击，在以下场景中存在明显不足：

- 新用户行为较少，容易陷入冷启动，只能反复推荐热门内容。
- 用户点击、停留、跳过和 Dislike 等信号强弱不同，简单累计难以正确表达兴趣。
- 用户无法通过“不要悬疑”“多推荐历史”“想看国风”等自然语言即时调整结果。
- 低曝光内容难以进入候选集，推荐列表的多样性和新颖性不足。
- 引入大模型后，如果直接替换原推荐链路，难以复用已有召回和排序分数，也缺少安全的降级边界。

本项目提供了一条可验证的原型链路：解析用户指令，更新会话画像，合并传统、语义和长尾候选分数，应用负反馈约束和多样性重排，最后返回推荐结果、推荐理由和结构化排序证据。

## 主要功能

### 1. 自然语言指令解析

当前规则解析器支持：

- 正向偏好：例如“喜欢历史”“想看悬疑”。
- 负向偏好：例如“不要美食”“不喜欢科幻”。
- 画风偏好：国风、写实、二次元、极简、复古、赛博朋克、治愈、暗黑。
- 探索意图：例如“随便看看”“换点新鲜的”。
- 偏好重置：例如“重置偏好”“重新开始”。
- 解释意图识别：例如“为什么推荐这个”。

### 2. 用户画像和行为反馈

- 记录点击、喜欢、Dislike、跳过和曝光行为。
- 根据行为发生时间进行 30 天指数衰减。
- 点击权重会结合停留时长调整。
- 重复 Dislike 会动态增强负向权重，并设置上限。
- 显式新指令可以覆盖已有的相反兴趣。

画像目前保存在进程内的 `InMemoryProfileStore` 中，服务重启后数据会丢失。

### 3. 混合召回与精排

- 融合 Legacy 分数、标签语义重合度和低曝光探索分数。
- 将兴趣匹配、显式请求、负反馈风险、画风、质量和新颖度构造成结构化排序特征。
- 对强负反馈内容执行过滤，对其他候选进行加权精排。
- 对新用户提高探索权重。
- 使用 MMR 思路降低已选结果之间的标签相似度，提高列表多样性。

### 4. 对话式推荐

同一个 `user_id` 的多轮请求会持续更新画像。例如用户先说“喜欢历史和悬疑”，下一轮说“不要悬疑了”，后续结果会过滤悬疑内容。

### 5. 推荐解释与可审计信息

每个结果包含：

- 推荐分数；
- 面向用户的简短理由；
- `reason_codes`；
- 精排使用的结构化特征。

项目不会返回模型的自由文本思维链。

### 6. 联合 Token 训练辅助代码

`training.py` 可以构造自然语言与 `<ITEM_id>`、行为 Token 交错的训练样本，并提供推荐 Token 交叉熵、文本交叉熵和对齐损失的加权公式。它是框架无关的样本/损失参考实现，**不包含完整的 Seed 微调任务或模型权重**。

### 7. HTTP API

- `GET /health`：健康检查。
- `POST /v1/recommend/chat`：提交自然语言需求并获取推荐。
- `POST /v1/recommend/feedback`：上报点击、喜欢、Dislike、跳过或曝光行为。
- `/docs`：FastAPI 自动生成的 Swagger 文档。

## 环境要求

- Python 3.10 或更高版本
- Windows PowerShell、macOS 或 Linux Shell

核心推荐代码仅使用 Python 标准库。启动 HTTP 服务需要 FastAPI 和 Uvicorn，运行测试需要 Pytest，这些依赖均已配置在 `pyproject.toml` 中。

## 安装方法

先进入项目目录：

```powershell
cd "基于 Seed 大模型的对话式推荐 Agent 系统研发"
```

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[api,dev]"
```

如果系统限制 PowerShell 激活脚本，也可以不激活虚拟环境，直接使用：

```powershell
.venv\Scripts\pip install -e ".[api,dev]"
```

### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[api,dev]"
```

## 使用方法

### 方法一：运行命令行演示

Windows：

```powershell
.venv\Scripts\python scripts\demo.py
```

macOS / Linux：

```bash
.venv/bin/python scripts/demo.py
```

演示会使用相同用户连续发起两轮请求，展示负向指令对上一轮偏好的覆盖效果。

### 方法二：启动 HTTP 服务

Windows：

```powershell
.venv\Scripts\uvicorn seed_rec_agent.api:app --host 127.0.0.1 --port 8000
```

macOS / Linux：

```bash
.venv/bin/uvicorn seed_rec_agent.api:app --host 127.0.0.1 --port 8000
```

启动后可访问：

- Swagger：<http://127.0.0.1:8000/docs>
- 健康检查：<http://127.0.0.1:8000/health>

### 方法三：在 Python 中调用

```python
from seed_rec_agent.agent import RecommendationAgent
from seed_rec_agent.retrieval import HybridRetriever
from seed_rec_agent.sample_data import sample_catalog

agent = RecommendationAgent(HybridRetriever(sample_catalog()))

response = agent.chat(
    user_id="u-demo",
    session_id="s-demo",
    message="我喜欢历史和悬疑，想看国风",
    limit=3,
)

for item in response.recommendations:
    print(item.title, item.score, item.reason)
```

### 运行测试

```powershell
pytest -q
```

测试覆盖指令解析、显式负反馈过滤、画风偏好、多轮偏好覆盖、行为反馈、结构化 trace、联合 Token 样本和损失公式。

## 输入输出示例

### 命令行多轮对话

输入：

```text
我喜欢历史和悬疑，想看国风
```

实际样例输出：

```text
Agent：已根据你的最新要求调整推荐。
- 长安十二时辰解析 (0.843)：符合你对历史、悬疑的当前需求
- 宋代服饰复原 (0.690)：符合你对历史的当前需求
- 治愈系森林料理 (0.311)：综合你的近期兴趣与内容质量推荐
```

第二轮输入：

```text
不要悬疑了，换点新鲜的
```

实际样例输出：

```text
Agent：已根据你的最新要求调整推荐。
- 宋代服饰复原 (0.559)：匹配你偏好的国风画风
- 治愈系森林料理 (0.311)：综合你的近期兴趣与内容质量推荐
- 极简居家改造 (0.302)：综合你的近期兴趣与内容质量推荐
```

第二轮结果不再包含带有“悬疑”标签的《长安十二时辰解析》。以上分数由仓库当前样例数据和排序参数产生；修改数据、参数或用户历史后，输出会相应变化。

### 对话推荐 API

请求：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/v1/recommend/chat" `
  -H "Content-Type: application/json" `
  -d '{"user_id":"u-demo","session_id":"s-demo","message":"我喜欢历史，想看国风","limit":2}'
```

请求体字段：

| 字段 | 类型 | 约束 | 含义 |
|---|---|---|---|
| `user_id` | string | 必填 | 用户标识，也是当前内存画像的索引 |
| `session_id` | string | 必填 | 会话标识，会原样返回 |
| `message` | string | 1～500 字符 | 当前自然语言指令 |
| `limit` | integer | 1～20，默认 5 | 返回条数上限 |

响应结构示例（`request_id` 每次调用都会变化）：

```json
{
  "session_id": "s-demo",
  "message": "已根据你的最新要求调整推荐。",
  "recommendations": [
    {
      "item_id": "i1",
      "title": "长安十二时辰解析",
      "score": 0.70959,
      "reason": "符合你对历史的当前需求",
      "trace": {
        "reason_codes": ["explicit_request", "style_match"],
        "features": {
          "interest_match": 0.3799,
          "explicit_match": 1.0,
          "dislike_risk": 0.0,
          "style_match": 1.0,
          "quality": 0.92,
          "legacy_score": 0.898,
          "semantic_score": 0.3333,
          "novelty": 0.0353,
          "exploration": 0.2171
        }
      }
    }
  ],
  "parsed_intent": {
    "positive_tags": ["历史"],
    "negative_tags": [],
    "styles": ["国风"],
    "reset": false,
    "explore": false,
    "explanation": false
  },
  "request_id": "每次请求生成的 UUID"
}
```

`recommendations` 最多返回 `limit` 条；若强负向约束过滤了所有候选，列表可能为空。集合类型字段在 JSON 中会被编码为数组，数组顺序不应作为业务约定。

### 反馈 API

上报一次对科幻内容的 Dislike：

```powershell
curl.exe -X POST "http://127.0.0.1:8000/v1/recommend/feedback" `
  -H "Content-Type: application/json" `
  -d '{"user_id":"u-demo","item_id":"i6","event":"dislike","tags":["科幻"]}'
```

成功响应：

```json
{
  "status": "accepted"
}
```

`event` 可选值为 `click`、`like`、`dislike`、`skip`、`expose`。`item_id` 必须存在于当前目录数据中，否则接口返回 HTTP 404。调用方应在 `tags` 中传入该内容需要影响画像的标签；当前接口不会根据 `item_id` 自动补全标签。

## 项目结构

```text
.
├── pyproject.toml
├── scripts/
│   └── demo.py                  # 两轮对话演示
├── src/seed_rec_agent/
│   ├── agent.py                 # Agent 主流程
│   ├── api.py                   # FastAPI 接口
│   ├── intent.py                # 规则指令解析
│   ├── models.py                # 领域数据模型
│   ├── profile.py               # 用户画像和反馈更新
│   ├── retrieval.py             # 混合召回
│   ├── ranking.py               # 特征构造、精排和多样性重排
│   ├── seed_adapter.py          # Seed 协议与本地解释适配器
│   ├── store.py                 # 内存画像存储
│   ├── sample_data.py           # 8 条演示内容
│   └── training.py              # 联合 Token 样本与损失参考
└── tests/                        # 自动化测试
```

## 当前限制与生产接入

- 指令解析当前是规则实现，不是大模型意图识别服务。
- `LocalSeedAdapter` 只根据匹配结果生成确定性文案，没有调用真实 Seed 模型。
- 候选集来自 8 条内置样例数据，没有连接向量数据库、搜索服务或线上推荐系统。
- 用户画像只保存在单进程内存中，不支持持久化和多实例共享。
- 当前 API 是同步实现，未包含鉴权、限流、超时、熔断和监控。
- 联合 Token 模块只负责构造样本与计算参考损失，不执行模型训练。

生产接入时，可以分别替换 `SeedModel`、`HybridRetriever` 和 `InMemoryProfileStore`，接入真实 Seed RPC、已有召回/多任务排序服务以及 Redis/特征平台。更完整的设计说明见 [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)。
