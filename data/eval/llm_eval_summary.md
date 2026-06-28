# Foretell LLM Eval Phase 1 Summary

- **Phase**: LLM Eval MVP (三智能体：Requirement Analyst → Path Explorer → Review)
- **P0 types**: A08, A17, X05, X06, X12, B01, B09, E05, G01, G07
- **Evaluated at**: 2026-06-28
- **Baseline verified**: probe_cases 120, jsonl 120, taxonomy 120, test_cases 10 (G07 from probe_cases)

## Completion Stats

| Deliverable | Count | Status |
|-------------|-------|--------|
| atomic_decompositions | 10/10 | ✅ |
| path_attempts | 10/10 | ✅ (real tool runs) |
| answer_playbooks | 10 entries | ✅ |
| route_matrix_merged | 10 P0 entries | ✅ |
| agent definitions | 3 | ✅ |
| orchestration scripts | llm_eval_common + run_llm_eval_phase1 | ✅ |

## Pass / Fail Distribution

| Result | Count | Types |
|--------|-------|-------|
| **PASS** | 5 | A08, A17, X05, X06, X12 |
| **FAIL** | 5 | B01, B09, E05, G01, G07 |

- **Pass rate**: 50% (5/10)
- **route_complete** (path explorer): 5/10 fully satisfied atomics without blocking_gap
- **Average llm_eval_score**: 3.46 (pass types avg 4.26, fail types avg 2.62)

## Score Highlights

| type_id | overall | pass | blocking_gap |
|---------|---------|------|--------------|
| X05 | 4.45 | ✅ | — |
| A08 | 4.40 | ✅ | — |
| A17 | 4.43 | ✅ | — |
| X06 | 4.18 | ✅ | — |
| X12 | 4.05 | ✅ | — (swap 挪威主场) |
| E05 | 3.35 | ❌ | implementation_gap |
| G07 | 2.95 | ❌ | implementation_gap |
| G01 | 2.45 | ❌ | data_gap |
| B09 | 2.35 | ❌ | data_gap |
| B01 | 1.95 | ❌ | data_gap |

## Top 5 Gaps (Phase 2 Recommendations)

1. **data_gap — lottery 场次解析** (B01, G01): `resolve_lottery_match` 对历史/模板场次返回 ENTITY_NOT_FOUND；需补 lottery 表覆盖或 date/code 映射策略。
2. **data_gap — NBA series_game** (B09): `resolve_match(series_game=7)` → NOT_APPLICABLE；篮球季后赛 G 场次维度未入库。
3. **implementation_gap — 深度分析 stub 链** (B01, E05, G07): `get_recent_form`, `get_odds_snapshot`, `get_injury_report` 等待 mysql_client 实装。
4. **routing_gap — 主客场入库 vs 用户表述** (X12): 2026-06-27 法国 vs 挪威 以「挪威 vs 法国」存储；Skill/entity-resolution 需 swap 或候选消歧指引。
5. **routing_gap — 多轮 context / G 场景** (G01, G07): follow-up 与跨窗口引用依赖 checkpointer；Phase1 仅 atomic 分解 + 单会话 tool 探路。

## Phase 2 Recommendations

1. **P0 失败项优先**：B01 lottery 数据补全 → E05 stub 工具实装 → G01/G07 context 策略。
2. **保留 verified 五条** (A08/A17/X05/X06/X12) 作为 regression baseline；接入 `tests/eval/test_tool_chain.py`（不修改现有 test_cases.yaml）。
3. **扩展 path explorer**：将 X12 home-away swap 沉淀为 entity-resolution 文档（非 Phase1 改 skills）。
4. **G07 升格 P0 测试用例**：test_cases.yaml 仍缺 G07，建议 Phase2 增补 TC-G07-001。
5. **discover_via_search**：Phase1 全部 skipped；Phase2 可选 Tavily 对照组，单独 wave。

## Artifacts

```
data/eval/atomic_decompositions/{A08,A17,X05,X06,X12,B01,B09,E05,G01,G07}.yaml
data/eval/path_attempts/{same}.yaml
data/eval/answer_playbooks.yaml
data/eval/route_matrix_merged.yaml
.cursor/agents/requirement-analyst-agent.md
.cursor/agents/path-explorer-agent.md
.cursor/agents/review-agent.md
scripts/llm_eval_common.py
scripts/run_llm_eval_phase1.py
```

## Blockers

- None for Phase1 deliverable completion.
- **Runtime dependency**: MySQL via `.env` for path exploration; runs succeeded 2026-06-28.
- B01/G01 lottery ENTITY_NOT_FOUND is **expected** documented data_gap, not script failure.
