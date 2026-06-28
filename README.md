# learnlangchain — Foretell 智能体

基于 [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) 框架构建的体育赛事智能助手 **Foretell**。

## 项目结构

```
learnlangchain/
├── api/                 # FastAPI HTTP 入口
├── config/              # 模型与环境配置
└── foretell/            # Foretell 智能体
    ├── agent.py         # create_foretell_agent()
    ├── prompts.py       # 系统提示词
    ├── tools/           # 业务工具（赛程、实体、盘口等）
    ├── skills/          # 按需加载的领域技能
    └── AGENTS.md        # 跨会话偏好记忆
```

## 快速开始

1. 安装依赖：

```bash
uv sync
```

2. 配置环境变量（复制 `.env.example` 为 `.env` 并填入密钥）：

```bash
cp .env.example .env
```

3. 启动 API 服务：

```bash
uv run uvicorn api.main:app --reload
```

端点：`GET /health`、`POST /v1/chat`（支持 `stream: true` 的 SSE 流式）。

## Foretell 能力

| 层级 | 能力 |
|------|------|
| **Harness 内置** | 任务规划、子 Agent 委派、按需加载技能 |
| **自定义工具** | 赛程查询、实体定位、统计、盘口、深度情报等 |
| **技能** | 轻量查询、赛事分析、购彩参考、批量筛选等场景 Skill |
| **记忆** | Checkpointer 多轮对话；`/memories/` 跨会话偏好 |

## 开发工具链

代码质量由 **ruff（lint + format）+ mypy（类型）+ pre-commit** 守护。

```bash
# 安装依赖（含 ruff / mypy / prod Checkpointer 等）
uv sync

# 检查 / 格式化 / 类型
uv run ruff check          # lint
uv run ruff format --check # 格式校验（写回用 --check 去掉）
uv run mypy                # 类型（仅扫 foretell/ api/ config/）

# 测试
uv run pytest

# Git 提交钩子（首次执行一次）
uv run pre-commit install
```

提交时 pre-commit 会自动跑 ruff 与基础检查；完整测试和类型检查在本地执行。

