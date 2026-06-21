# Foretell 自托管实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or executing-plans. Steps use checkbox syntax.

**Goal:** 按 spec 将 Foretell 从调研原型重构为自托管体育赛事问答智能体（Deep Agents + FastAPI + Mock/真实 DB Tools）。

**Architecture:** Checkpointer 承担会话上下文；Harness 使用 StateBackend；业务数据经 Tool envelope 访问；深度分析由子智能体 task 返回 JSON 后主智能体归纳。

**Tech Stack:** Python 3.14+, deepagents, langgraph, FastAPI, uvicorn, pytest, Postgres（Phase 4）

## Global Constraints

- 部署：自托管 Postgres + 自建 API
- 无代码沙箱、无 Swarm
- 生产禁止 FilesystemBackend 作为 default
- 购彩回复结尾必须含「⚠️ 彩票有风险，投注需谨慎」
- 不暴露工具名/字段名；不输出「正在查询」中间态
- 会话态靠 Checkpointer，不做 match_context Store 键
- 状态码在 Tool 层判定，LLM 不猜

---

## Phase 0 — 基础设施骨架

### Task 0.1 Git 与文档基线

**Files:** `docs/DEVELOPMENT.md`, `.gitignore`

- [ ] 初始提交项目 scaffold
- [ ] 创建 `develop`、`feature/foretell-phase-0-infra` 分支
- [ ] 确认 `.env` 在 gitignore

### Task 0.2 配置层

**Files:** `config/settings.py`, `.env.example`

- [ ] 增加 `DEPLOY_ENV`（dev/prod）、`DATABASE_URL`
- [ ] 增加 `CRAZY_SPORTS_API_BASE`、`CRAZY_SPORTS_API_KEY`（可空，Mock 用）
- [ ] 增加 `API_HOST`、`API_PORT`、`JWT_SECRET`（dev 默认）
- [ ] `get_settings()` 单例或 dataclass

### Task 0.3 Backend 工厂

**Files:** `foretell/backends.py`

- [ ] `create_checkpointer(env)` → MemorySaver | PostgresSaver
- [ ] `create_store(env)` → InMemoryStore | PostgresStore（可选 None）
- [ ] `create_agent_backend(runtime)` → StateBackend
- [ ] dev/prod 由 `DEPLOY_ENV` 切换

### Task 0.4 Agent 重构

**Files:** `foretell/agent.py`, `foretell/prompts.py`, `foretell/AGENTS.md`

- [ ] 移除 FilesystemBackend default、CompositeBackend（除非 /memories/）
- [ ] 使用 `create_agent_backend` + `create_checkpointer`
- [ ] system prompt 改为体育助手定位（占位，Phase 1 细化）
- [ ] `create_foretell_agent(deploy_env="dev")` 签名
- [ ] configurable 支持 `user_id` + `thread_id`

### Task 0.5 FastAPI 骨架

**Files:** `api/__init__.py`, `api/main.py`, `api/auth.py`, `api/schemas.py`

- [ ] `GET /health`
- [ ] `POST /v1/chat` — body: message, thread_id?, stream?
- [ ] dev 鉴权：Header `X-User-Id` 或 JWT stub → `user_id`
- [ ] `thread_id` 默认 `{user_id}:{uuid}`
- [ ] 调用 agent.invoke，返回 assistant 内容
- [ ] pyproject 增加 `fastapi`, `uvicorn[standard]`, `python-jose`（可选）

### Task 0.6 CLI 适配

**Files:** `main.py`

- [ ] `--user-id` 参数；config 传入 user_id
- [ ] thread_id 格式与 API 一致

### Task 0.7 Phase 0 测试

**Files:** `tests/conftest.py`, `tests/unit/test_backends.py`, `tests/unit/test_api_health.py`

- [ ] pytest 配置
- [ ] backend 工厂 dev 返回 MemorySaver
- [ ] TestClient `/health` 200

**Commit:** `feat(infra): phase 0 skeleton — backends, api, agent refactor`

---

## Phase 1 — Tool 层 + 场景 A

### Task 1.1 状态码与 Envelope

**Files:** `foretell/tools/status_codes.py`, `foretell/tools/envelope.py`

- [ ] `StatusCode` enum、`PlayType` enum（101/201/…）
- [ ] `make_envelope(code, dimension, data, match_id?, meta?)`
- [ ] 单元测试覆盖各 code

### Task 1.2 Mock 疯狂体育客户端

**Files:** `foretell/tools/crazy_sports/client.py`, `foretell/tools/crazy_sports/mock_data.py`

- [ ] 抽象 `CrazySportsClient` 协议
- [ ] `MockCrazySportsClient` 固定样本数据
- [ ] 工厂：`get_crazy_sports_client()` 读 settings

### Task 1.3 实体与赛程 Tools

**Files:** `foretell/tools/entity.py`, `foretell/tools/schedule.py`, `foretell/tools/__init__.py`

- [ ] `resolve_match`, `resolve_lottery_match`, `resolve_team`, `resolve_league`
- [ ] `get_schedule_by_date`, `get_team_schedule`, `get_lottery_schedule`
- [ ] 全部返回 envelope JSON 字符串

### Task 1.4 Skills（公共 + A）

**Files:** `foretell/skills/foretell-entity-resolution/SKILL.md`, `foretell-status-dictionary/SKILL.md`, `foretell-output-discipline/SKILL.md`, `foretell-light-query/SKILL.md`

- [ ] 删除或迁移旧 `research-report` skill
- [ ] 四个 Skill 含 YAML frontmatter

### Task 1.5 Agent 接线

**Files:** `foretell/agent.py`, `foretell/prompts.py`

- [ ] 注册 Phase 1 tools
- [ ] skills 路径更新

**Commit:** `feat(tools): phase 1 mock db tools and light-query skills`

---

## Phase 2 — 子智能体 + 场景 B/G

### Task 2.1 统计/盘口 Tools

**Files:** `foretell/tools/stats.py`, `foretell/tools/odds.py`, `foretell/tools/deep.py`

- [ ] get_standings, get_recent_form, get_h2h, get_odds_snapshot, get_match_lineup 等

### Task 2.2 子智能体定义

**Files:** `foretell/subagents/__init__.py`, `foretell/subagents/definitions.py`

- [ ] entity-resolver, fundamentals-analyst, odds-analyst, intel-analyst
- [ ] 各子智能体 tools + system_prompt + skills

### Task 2.3 Skills B/G

**Files:** `foretell-match-analysis/SKILL.md`, `foretell-follow-up/SKILL.md`

### Task 2.4 集成测试

**Files:** `tests/integration/test_follow_up_chain.py`

- [ ] 固定 thread_id 多轮：分析 → 比分预测 → 先进球

**Commit:** `feat(agent): phase 2 subagents and match analysis`

---

## Phase 3 — 剩余场景 C/D/E/F/H

- [ ] Skills + tools 补齐
- [ ] screening-agent 批量初筛
- [ ] 购彩护栏 prompt 测试

**Commit:** `feat(skills): phase 3 remaining scenarios`

---

## Phase 4 — 生产硬化

- [ ] PostgresSaver/Store 连接池
- [ ] SSE 流式 `/v1/chat`
- [ ] 真实 CrazySportsClient
- [ ] LangSmith 评估集

**Commit:** `feat(api): phase 4 production postgres and streaming`

---

## 验收清单（每 Phase）

1. `uv run pytest` 全绿
2. reviewer 子智能体无 blocking 问题
3. 合并到 `develop` 并打 tag `foretell-phase-N`
