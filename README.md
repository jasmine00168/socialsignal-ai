# SocialSignal AI

> 从社交媒体原帖中识别软件需求，保留证据，并形成可验证的机会洞察。

SocialSignal AI 是一个面向产品经理、创业者和增长团队的 AI 需求研究工具。它将零散的社交媒体表达转化为结构化需求，同时保留原帖链接和逐字证据，帮助团队区分“看起来热门的话题”和“值得进一步验证的产品机会”。

## 当前可体验功能 · V0.1

- 使用内置匿名演示数据，或上传自己的 CSV。
- 调用 OpenAI Responses API 判断帖子是否包含软件需求。
- 使用 Structured Outputs 提取目标用户、使用场景、痛点和期望方案。
- 输出紧迫度、置信度和付费意愿信号。
- 自动验证 AI 引用是否逐字存在于原帖。
- 查看完整结构化 JSON，便于审查 AI 的数据契约。

## 产品流程

```text
社交媒体帖子
    ↓
数据字段校验
    ↓
AI 结构化需求提取
    ↓
原文证据自动校验
    ↓
可审查的需求卡片
```

V0.1 的重点不是抓取尽可能多的数据，而是先验证最小价值闭环：**一条帖子能否被稳定识别、结构化，并追溯到原文证据。**

## 快速开始

推荐 Python 3.11 或 3.12。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env.local
streamlit run app.py
```

在 `.env.local` 中配置：

```dotenv
OPENAI_API_KEY=your_key_here
OPENAI_MODEL=gpt-5.4-mini
```

`.env.local` 已被 Git 忽略，禁止把真实 API Key 提交到仓库。

### API 连通性测试

以下命令会产生一次真实 API 请求和少量费用：

```powershell
python scripts/smoke_api.py
```

成功时只显示需求判断、机会标题、证据校验结果和模型名称，不显示密钥。

### 运行离线测试

```powershell
python -m unittest discover -s tests -v
```

## CSV 数据格式

必要字段：

| 字段 | 含义 |
| --- | --- |
| `post_id` | 帖子唯一编号 |
| `platform` | 来源平台 |
| `content` | 原帖正文 |
| `source_url` | 原帖链接或脱敏证据地址 |

可选字段：`likes`、`comments`、`published_at`。

仓库中的演示数据为虚构内容，不代表真实用户或真实平台帖子。

## AI 输出数据契约

每条帖子会输出：

- 是否存在需求及需求类型
- 机会标题
- 目标用户与使用场景
- 核心痛点与期望方案
- 当前替代方式
- 付费意愿信号
- 紧迫度与置信度
- 逐字原文证据
- 证据是否通过程序校验
- 模型名称和原帖编号

Structured Outputs 用于约束字段类型；程序校验用于检查证据是否真的来自原帖。两层机制共同降低模型输出不可控的问题。

## 产品边界

当前版本暂不包含：

- 未经授权的平台自动抓取
- 多账号登录和集中管理
- 自动发布社交媒体内容
- 仅依据点赞量推断市场规模

这些能力涉及平台权限、数据合规和误发风险，会在核心需求识别能力验证后单独评估。

## Roadmap

- [x] V0.1：单条需求识别、结构化输出、证据校验
- [ ] V0.2：批量分析、相似需求聚类、机会评分
- [ ] V0.3：需求看板、证据详情、机会报告导出
- [ ] V0.4：内容工作台、人工审核发布队列
- [ ] V1.0：评测集、质量指标、成本监控、公开部署

## 产品文档

- [`docs/PRODUCT_BRIEF.md`](docs/PRODUCT_BRIEF.md)：目标用户、JTBD、范围、成功指标和产品风险。
- [`AGENTS.md`](AGENTS.md)：项目架构与 AI 开发约束。

## 技术栈

- Python
- Streamlit
- pandas
- OpenAI Responses API
- Pydantic / JSON Schema
- unittest
