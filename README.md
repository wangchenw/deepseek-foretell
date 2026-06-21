# learnlangchain — Foretell 智能体

基于 [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) 框架构建的深度研究与趋势研判智能体 **Foretell**。

## 项目结构

```
learnlangchain/
├── config/              # 模型与环境配置
├── foretell/            # Foretell 智能体
│   ├── agent.py         # create_foretell_agent()
│   ├── prompts.py       # 系统提示词
│   ├── tools/           # 自定义工具（互联网搜索等）
│   ├── skills/          # 按需加载的领域技能
│   └── AGENTS.md        # 跨会话偏好记忆
├── data/workspace/      # Agent 输出报告的工作区
└── main.py              # 命令行入口
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

3. 运行 Foretell：

```bash
# 单次提问
uv run python main.py "2026年 AI Agent 有哪些重要趋势？"

# 交互模式
uv run python main.py

# 保持同一会话上下文
uv run python main.py --thread-id my-session
```

## Foretell 能力

| 层级 | 能力 |
|------|------|
| **Harness 内置** | 任务规划、文件读写、子 Agent 委派 |
| **自定义工具** | `internet_search`（Tavily 搜索） |
| **技能** | `research-report` — 结构化研究报告撰写 |
| **记忆** | `/memories/` 跨会话持久化，`/data/workspace/` 报告输出 |
