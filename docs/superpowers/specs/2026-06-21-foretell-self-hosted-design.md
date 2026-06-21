# Foretell 体育赛事智能助手 — 自托管架构设计 Spec

> 状态：已批准 · 持久化以 Checkpointer 为主（2026-06-21 修订）  
> 日期：2026-06-21  
> 部署形态：**自托管（Postgres + 自建 API）**  
> 产品依据：`Foretell产品.md`

---

## 1. 目标与范围

### 1.1 产品目标

构建问答式体育赛事智能助手，覆盖足球/篮球及中国体育彩票场景。用户用自然语言提问，系统完成：

1. 实体识别与场次定位（先定位，再查询）
2. 自动调用疯狂体育结构化数据库（不经 LLM 写 SQL）
3. 子智能体分维度统计分析，主智能体按场景 Skill 归纳输出
4. 多轮追问与跨会话上下文延续
5. 购彩场景安全护栏

### 1.2 非目标

- **不需要代码沙箱**（无用户代码执行、无 E2B/Docker 解释器）
- **不使用 Swarm / QuickJS**（批量场景用 `task` 子智能体并行即可）
- **不承诺** LangGraph Platform 托管（选定自托管）

### 1.3 与现有代码的关系

当前 `foretell/` 为「深度调研 + 互联网搜索」原型（`MemorySaver`、`FilesystemBackend`、`internet_search`）。本 spec 描述**目标架构**；实现时需将 agent、prompt、tools、skills 整体替换为体育问答能力，保留 `create_deep_agent` + `CompositeBackend` 骨架。

---

## 2. 自托管部署架构

### 2.1 总体拓扑

```
┌─────────────┐     HTTPS      ┌──────────────────┐
│  Web / App  │ ──────────────▶│  Foretell API    │
│  客户端      │                │  (FastAPI 等)     │
└─────────────┘                └────────┬─────────┘
                                          │
                    configurable: { user_id, thread_id }
                                          ▼
                                 ┌──────────────────┐
                                 │  Deep Agents     │
                                 │  foretell agent  │
                                 └────────┬─────────┘
                          ┌───────────────┼───────────────┐
                          ▼               ▼               ▼
                   ┌────────────┐  ┌────────────┐  ┌──────────────┐
                   │ PostgreSQL │  │ PostgreSQL │  │ 疯狂体育 DB  │
                   │ Checkpointer│  │ Store      │  │ (HTTP/RPC)   │
                   │ 对话状态    │  │ 会话键值    │  │ 只读 Tool    │
                   └────────────┘  └────────────┘  └──────────────┘
```

### 2.2 组件职责

| 组件 | 技术选型 | 职责 |
|------|----------|------|
| API 层 | FastAPI（推荐） | 鉴权、`user_id` 注入、`thread_id` 管理、流式 SSE |
| Agent | `create_deep_agent` | 意图路由、Skill 加载、子智能体委派、最终归纳 |
| Checkpointer | `PostgresSaver` | 同 thread 多轮对话、最近 6 轮上下文 |
| Store | `PostgresStore`（可选） | 仅 `user_prefs` 等跨 thread 偏好；会话态靠 Checkpointer |
| 业务 DB | 疯狂体育 API | 赛程、统计、盘口；仅 Tool 层访问 |

### 2.3 环境变量（最小集）

```bash
# LLM
OPENAI_API_KEY=...          # 或所用 provider

# LangSmith（推荐）
LANGSMITH_API_KEY=...
LANGSMITH_TRACING=true
LANGSMITH_PROJECT=foretell

# 自托管持久化
DATABASE_URL=postgresql://user:pass@host:5432/foretell

# 疯狂体育
CRAZY_SPORTS_API_BASE=...
CRAZY_SPORTS_API_KEY=...
```

### 2.4 开发 vs 生产

| 阶段 | Checkpointer | Store | Backend 默认层 |
|------|--------------|-------|----------------|
| 本地开发 | `MemorySaver` | `InMemoryStore` | `StateBackend` |
| 生产 | `PostgresSaver` | `PostgresStore` | `StateBackend` |

生产环境**禁止**对 Web 请求使用 `FilesystemBackend` 作为 default（避免越权读盘）。Skills 在进程启动时写入 Store，或只读挂载固定 `skills/` 目录。

---

## 3. 持久化设计（极简 · Checkpointer 为主）

不构建多层虚拟目录。**会话上下文 = Checkpointer 对话历史**；子智能体结果经 `task` 返回值带回，不落盘。

### 3.1 分工

| 存储 | 职责 | 生命周期 |
|------|------|----------|
| **Checkpointer** | 消息历史、`write_todos`、多轮追问上下文 | 按 `thread_id` |
| **Store**（可选） | 仅 `user_prefs` 等跨 thread 偏好 | 跨会话 |

**刻意不做：**

- `match_context` Store 键 — 同 thread 内靠对话历史；实测定位出错再加
- `/drafts/`、`/sessions/`、`/cache/matches/` 虚拟目录
- 跨会话记住比赛分析

场景 G（比分预测、先进球、继续）：读取 Checkpointer 中最近对话及已生成的六段分析，不重复定位。

### 3.2 Backend（Harness 最小配置）

Deep Agents 文件工具需要 Backend；Foretell 业务态不依赖虚拟文件路径。

```python
# 推荐：纯 StateBackend
backend=lambda rt: StateBackend(rt)

# 若使用 AGENTS.md 跨会话偏好，可加：
CompositeBackend(default=StateBackend(rt), routes={"/memories/": StoreBackend(rt)})
```

Skills：开发环境只读挂载 `foretell/skills/`。**生产禁止** `FilesystemBackend` 作为 default。

---

## 4. 用户隔离

### 4.1 API 层

每个请求必须携带已鉴权的 `user_id`。API 生成或校验 `thread_id`：

```python
config = {
    "configurable": {
        "user_id": user_id,
        "thread_id": f"{user_id}:{session_id}",
    }
}
```

### 4.2 Store 命名空间（可选，仅跨 thread 偏好）

```python
store.put(("foretell", user_id), "user_prefs", {"lang": "zh"})
```

会话态不在 Store 中维护；由 Checkpointer 对话历史承担。

### 4.3 隔离规则

- 不同用户禁止共享 `thread_id`
- 所有 Store 读写 namespace 必须含 `user_id`
- 用户分析结果与会话态不可跨用户共享

---

## 5. API 层设计（自建）

### 5.1 核心端点

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/v1/chat` | 同步或流式对话 |
| GET | `/v1/threads/{thread_id}` | 获取会话元数据（可选） |
| DELETE | `/v1/threads/{thread_id}` | 用户删除会话（可选） |
| GET | `/health` | 健康检查 |

### 5.2 请求体

```json
{
  "message": "分析竞彩足球周二004 巴黎 VS 拜仁",
  "thread_id": "可选，省略则新建",
  "stream": true
}
```

### 5.3 流式输出

使用 LangGraph `stream_mode="messages"` 或等价 API，SSE 推送 token。遵守产品规范：**不输出**「正在查询」等中间态，仅流式最终回答内容。

### 5.4 鉴权

JWT / Session 解析出 `user_id`，不信任客户端传入的 `user_id` 字段。

---

## 6. 框架与编排

### 6.1 主框架

**Deep Agents**（`create_deep_agent`），理由：

- 内置 TodoList、SubAgent（`task`）、Skills、FilesystemMiddleware
- CompositeBackend + Store 跨会话
- 与现有 `foretell/agent.py` 骨架一致

### 6.2 主智能体职责

1. 理解意图，加载对应 Skill（A–H）
2. 决定是否调用 `entity-resolver` 子智能体
3. 选择轻量 / 深度 / 批量路径
4. 委派维度子智能体（深度路径），收集各 `task` 返回的结构化 JSON
5. 按场景 Skill 模板归纳输出
6. 依赖 Checkpointer 对话历史处理追问（场景 G）

### 6.3 子智能体

| 名称 | 工具 | 输出 |
|------|------|------|
| `entity-resolver` | `resolve_*` | `match_id`、定位证据 |
| `fundamentals-analyst` | 积分、近况、交锋、球员 | 结构化统计 JSON |
| `odds-analyst` | 欧赔、亚盘、大小球、走势、同赔 | 结构化统计 JSON |
| `intel-analyst` | 阵容、伤停、情报 | 结构化统计 JSON |
| `screening-agent` | 近况 + 盘口快查 | 初筛方向 + 置信度（非最终推荐） |

子智能体**无状态**：单次 `task` 调用须包含完整指令。自定义子智能体需**显式**挂载对应 skills。

### 6.4 深度分析数据流

```
用户提问
  → entity-resolver（如需）
  → 并行 task（各返回结构化 JSON，不写文件）:
       fundamentals-analyst → { stats, status_map, insights }
       odds-analyst         → { stats, status_map, insights }
       intel-analyst        → { stats, status_map, insights }
  → 主智能体在上下文中汇总
  → 按 foretell-match-analysis Skill 六段式输出
  → 写入 Checkpointer（后续追问读历史）
```

子智能体单次 `task` 返回示例：

```json
{
  "dimension": "fundamentals",
  "match_id": "m_12345",
  "stats": {"home_recent_5": {"W": 3, "D": 1, "L": 1}},
  "status_map": {"recent_form": "OK", "h2h": "DATA_MISSING"},
  "insights": ["主队主场强势"]
}
```

### 6.5 批量场景 E（扫盘 / 串关）

```
get_lottery_schedule → 场次列表
  → 对每个场次 task(screening-agent)  [可 asyncio 并发控制]
  → 主智能体聚合候选表
  → 用户要求「展开第 N 场」→ 走深度路径
  → 初筛与深核不一致：以深核为准并说明
```

---

## 7. Skills 目录规划

根目录：`foretell/skills/`（启动时加载或灌入 Store）

| Skill | 场景 | 描述要点 |
|-------|------|----------|
| `foretell-entity-resolution` | 公共 | 四种入口、G7 约束、兜底搜索 |
| `foretell-status-dictionary` | 公共 | 状态码 → 用户可见标注 |
| `foretell-output-discipline` | 公共 | 六段式、购彩护栏、术语 |
| `foretell-light-query` | A | 轻量查询、归纳优先 |
| `foretell-match-analysis` | B | 六段式深度分析 |
| `foretell-post-review` | C | 已完场复盘 |
| `foretell-betting-single` | D | 单场购彩 + 风险提示 |
| `foretell-batch-screening` | E | 初筛 / 深核两阶段 |
| `foretell-odds-query` | F | 快照 vs 走势消歧 |
| `foretell-follow-up` | G | 追问链、读 Checkpointer 历史 |
| `foretell-league-outlook` | H | 争冠保级语义精度 |

`AGENTS.md` 更新为体育助手偏好（语言、购彩免责、数据诚实）。

---

## 8. 数据库 Tool 层

### 8.1 原则

- 所有疯狂体育访问封装为 **LangChain Tool**
- Tool 返回统一 **envelope**，含 `code` 与 `dimension`
- **状态码在 Tool 层判定**，不由 LLM 猜测
- 让球方向使用 DB 中文表述，禁止 LLM 自行换算盘口

### 8.2 统一响应 Envelope

```json
{
  "code": "OK",
  "dimension": "european_odds",
  "match_id": "m_12345",
  "data": {},
  "meta": {"source": "crazy_sports_db", "freshness": "..."}
}
```

### 8.3 状态码表

| code | 用户标注 | 行为 |
|------|----------|------|
| `OK` | （正常分析） | 全权重 |
| `DATA_MISSING` | 数据不足 | 跳过该细项 |
| `NOT_APPLICABLE` | 不适用 + 原因 | 替代信息 |
| `SKIP_MATCH` | 盘口数据不足，建议跳过此场 | 欧赔+亚盘均缺 |
| `ENTITY_NOT_FOUND` | 未找到比赛 | 触发 Web 兜底（最多 1 次） |
| `PARTIAL` | 按维度分别标注 | 降权 |

### 8.4 Tool 清单（首期）

**实体层**

- `resolve_match(home, away, date?, series_game?)`
- `resolve_lottery_match(play_type, code, date?)`
- `resolve_team(name)` / `resolve_league(name)` / `resolve_player(name)`

**赛程层**

- `get_schedule_by_date(date, sport?, league_preset?)`
- `get_team_schedule(team_id, limit?)`
- `get_lottery_schedule(date?, play_type, period?)`

**统计层**

- `get_standings(league_id)` / `get_team_season_stats(team_id)`
- `get_recent_form(team_id, venue?, n=5)` / `get_h2h(team_a, team_b, n=5)`

**盘口层**

- `get_odds_snapshot(match_id)` / `get_odds_trend(match_id)`
- `get_same_odds_history(match_id)` / `get_kelly(match_id)` / `get_betfair(match_id)`

**深度层**

- `get_match_lineup(match_id)` / `get_injury_report(match_id)` / `get_intel_tags(match_id)`

**兜底**

- `web_search_fallback(query)` — 仅实体定位失败时使用

### 8.5 玩法编码

与产品文档一致：`101` 竞彩足球、`201` 竞彩篮球、`301` 北单胜负、`401` 十四场/任九等。Tool 参数使用枚举，不接受裸数字 magic number 字符串。

---

## 9. 安全与体验规范（强制）

写入 `foretell-output-discipline` Skill 与 system prompt：

- 购彩回复结尾：`⚠️ 彩票有风险，投注需谨慎`
- 同场同玩法单一主推；禁止矛盾双向推荐
- 不暴露工具名、字段名、内部 JSON 结构
- 不输出「正在查询」类中间态
- 非体育内容礼貌拒答
- 篮球禁用足球「胜平负」术语

---

## 10. 实施阶段

### Phase 0 — 基础设施（自托管骨架）

- [ ] `config/settings.py` 增加 `DATABASE_URL`、疯狂体育 API 配置
- [ ] `create_backend(deploy_env)` 工厂：dev 用 Memory，prod 用 Postgres
- [ ] FastAPI 最小 `/v1/chat` + JWT `user_id` 注入
- [ ] Postgres 建表（LangGraph checkpointer + store 迁移脚本）

### Phase 1 — Tool + 状态码 + 实体定位

- [ ] `foretell/tools/status_codes.py` + envelope  helper
- [ ] 实体层 + 赛程层 Tool（Mock 或真实 API）
- [ ] Skill：`foretell-entity-resolution`、`foretell-status-dictionary`
- [ ] 场景 A 轻量查询跑通

### Phase 2 — 场景 B/G

- [ ] 三维度子智能体 + `task` 返回 JSON + 六段式归纳
- [ ] Skill：`foretell-match-analysis`、`foretell-follow-up`
- [ ] 多轮追问（比分、先进球）依赖 Checkpointer 历史

### Phase 3 — 购彩与批量

- [ ] 场景 D 护栏 + 场景 E 初筛/深核
- [ ] 场景 F 赔率专项、场景 C 复盘、场景 H 宏观

### Phase 4 — 生产硬化

- [ ] PostgresSaver/Store 切换与连接池
- [ ] 流式 SSE、超时、并发限制
- [ ] LangSmith 追踪与评估数据集（竞彩 Top 问法）
- [ ] 移除 `FilesystemBackend` default（生产）

---

## 11. 测试策略

| 层级 | 内容 |
|------|------|
| Tool 单元测试 | 状态码映射、 envelope 形状、玩法枚举 |
| 集成测试 | 固定 `thread_id` 多轮追问链（产品附录旅程） |
| 回归集 | Top 14 竞彩模板问法 + 「继续」「比分预测」 |
| 人工评审 | 六段结构、购彩免责、让球中文表述 |

---

## 12. 待确认项（实现前）

1. 疯狂体育 API 文档与鉴权方式（内网 / 公网）
2. JWT 鉴权是否已有统一用户体系
3. 子智能体并行度上限（批量扫盘时的 QPS 限制）

---

## 13. 决策记录

| 决策 | 选择 | 理由 |
|------|------|------|
| 部署形态 | 自托管 Postgres + 自建 API | 用户确认；数据与隔离可控 |
| 执行沙箱 | 不需要 | 仅查库与分析，无用户代码执行 |
| 主框架 | Deep Agents | 子智能体、Skills、CompositeBackend |
| 批量并行 | `task` 子智能体 | 不引入 Swarm/QuickJS |
| 生产 Backend default | StateBackend | 避免 FilesystemBackend 线上越权 |
| POC | 本地 MemorySaver 可保留至 Phase 1 完成 | 降低早期搭建成本 |
| 持久化形态 | Checkpointer 为主 | 会话靠对话历史；Store 仅可选 user_prefs |
| 子智能体中间态 | `task` 返回 JSON | 不落虚拟文件 |
| 比赛 DB 缓存 | POC 不做 | 必要时在 Tool 层加 Redis/内存 |
