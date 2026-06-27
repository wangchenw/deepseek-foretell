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
  backends.py       # CompositeBackend + Skills 只读路由
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

## 疯狂体育 MySQL（data_center）

`.env` 配置（**勿提交 `.env`**）：

```bash
MYSQL_HOST=your-host
MYSQL_PORT=33306
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DATABASE=data_center
```

疯狂体育数据直接读取 `data_center` 库（`football_*`、`lottery_jczq_*` 等表）。

探针：`uv run python scripts/probe_mysql.py`

## 本地命令

```bash
uv sync
uv run pytest
uv run python main.py "今晚足球有什么"
uv run uvicorn api.main:app --reload
```

## 代码质量（ruff / mypy / pre-commit）

| 工具 | 作用 | 命令 |
|------|------|------|
| ruff | lint + 格式化 | `uv run ruff check` / `uv run ruff format --check` |
| mypy | 类型检查（仅 `foretell/ api/ config/`，非严格） | `uv run mypy` |
| pre-commit | 提交钩子（ruff + 基础卫生检查） | `uv run pre-commit run --all-files` |

配置位置：`pyproject.toml` 的 `[tool.ruff]`、`[tool.mypy]`；钩子定义：`.pre-commit-config.yaml`。

```bash
# 安装 dev 工具
uv sync --extra dev

# 首次启用提交钩子
uv run pre-commit install

# ruff 自动修复
uv run ruff check --fix
uv run ruff format
```

测试默认读取本地 `.env` 中的 MySQL 配置，需确保 `data_center` 可访问。



## 生产环境（Postgres）

生产部署需安装可选依赖组 `prod`，并设置 `DEPLOY_ENV=prod` 与 `DATABASE_URL`。

```bash
uv sync --extra prod
export DEPLOY_ENV=prod
export DATABASE_URL=postgresql://user:pass@localhost:5432/foretell
```

首次部署时，Checkpointer 与 Store 会调用 `setup()` 创建表结构（见 `foretell/backends.py`）。建议在部署迁移脚本中单独执行一次，避免应用启动时重复建表。

| 变量 | 说明 |
|------|------|
| `DEPLOY_ENV` | `dev`（MemorySaver）或 `prod`（PostgresSaver） |
| `DATABASE_URL` | PostgreSQL 连接串；`prod` 必填 |

开发环境无需 Postgres；会话态使用内存 Checkpointer。

## Skills Backend（Phase 5）

`SkillsMiddleware` 通过 Backend 虚拟路径加载 `foretell/skills/`，**不能**传磁盘绝对路径。

- `create_agent_backend()`：`CompositeBackend`，`default=StateBackend()`，`/skills/` → `FilesystemBackend(root_dir=foretell/skills, virtual_mode=True)`
- `create_foretell_agent`：`skills=["/skills/"]`
- 子智能体 `skills`：POSIX 路径，如 `/skills/foretell-entity-resolution/`
- MySQL `football_match.match_time` 为 Unix `int`；赛程查询用 `UNIX_TIMESTAMP`，勿用 `DATE(match_time)`

验收：`uv run pytest tests/integration/test_skills_loading.py -v`

## Phase 里程碑

- **Phase 0**：config、backend 工厂、FastAPI 骨架、agent 重构（StateBackend）
- **Phase 1**：status_codes、DB Tools、实体 Skill、场景 A
- **Phase 2**：子智能体 + 场景 B/G
- **Phase 3**：场景 C/D/E/F/H
- **Phase 4**：Postgres 生产、SSE 流式、LangSmith 评估
- **Phase 5**：Tool 消歧与 `match_time` 修复、Skills Backend、entity-resolver 赛程链、场景 A 路由
