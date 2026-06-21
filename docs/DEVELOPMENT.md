# Foretell 开发协作与 Git 工作流

## 目标

自托管 Foretell 体育赛事智能助手。架构 spec：`docs/superpowers/specs/2026-06-21-foretell-self-hosted-design.md`

## 分支策略

| 分支 | 用途 |
|------|------|
| `main` | 可发布基线；仅通过 PR 合并 |
| `develop` | 集成分支；各 Phase 完成后合并 |
| `feature/foretell-phase-N-*` | 功能开发；从 `develop` 拉出 |

## 提交规范

```
<type>(<scope>): <subject>

type: feat | fix | refactor | test | docs | chore
scope: agent | tools | api | skills | config
```

示例：`feat(tools): add status envelope and PlayType enum`

## 组件与职责（子智能体团队）

| 角色 | Cursor Agent | 职责 |
|------|--------------|------|
| 规划 | `planner` | 拆解 Phase 任务、文件清单 |
| 设计 | `brainstormer` / `analyst` | 接口设计、与 spec 对齐 |
| 开发 | `generalPurpose` | 实现代码 |
| 测试 | `tester` | pytest、集成用例 |
| 评审 | `reviewer` | Phase 完成门禁 |

主编排 Agent 负责：合并子智能体产出、git 分支、Phase 验收。

## 目录约定

```
foretell/
  agent.py          # create_foretell_agent
  backends.py       # StateBackend / Postgres 工厂
  prompts.py
  subagents/        # 子智能体定义
  tools/            # DB Tool + envelope
  skills/           # 场景 Skill (A-H)
api/
  main.py           # FastAPI
  auth.py           # user_id 注入
config/
  settings.py
tests/
  unit/
  integration/
docs/superpowers/
  specs/
  plans/
```

## 本地命令

```bash
uv sync
uv run pytest
uv run python main.py "今晚 NBA 有什么"
uv run uvicorn api.main:app --reload
```

## 生产环境（Postgres）

生产部署需安装可选依赖组 `prod`，并设置 `DEPLOY_ENV=prod` 与 `DATABASE_URL`。

```bash
uv sync --extra prod
export DEPLOY_ENV=prod
export DATABASE_URL=postgresql://user:pass@localhost:5432/foretell
```

首次部署时，Checkpointer 与 Store 会调用 `setup()` 创建表结构（见 `foretell/backends.py`）。建议在 CI/CD 迁移脚本中单独执行一次，避免应用启动时重复建表。

| 变量 | 说明 |
|------|------|
| `DEPLOY_ENV` | `dev`（MemorySaver）或 `prod`（PostgresSaver） |
| `DATABASE_URL` | PostgreSQL 连接串；`prod` 必填 |

开发环境无需 Postgres；会话态使用内存 Checkpointer。

## Phase 里程碑

- **Phase 0**：config、backend 工厂、FastAPI 骨架、agent 重构（StateBackend）
- **Phase 1**：status_codes、Mock DB Tools、实体 Skill、场景 A
- **Phase 2**：子智能体 + 场景 B/G
- **Phase 3**：场景 C/D/E/F/H
- **Phase 4**：Postgres 生产、SSE 流式、LangSmith 评估
