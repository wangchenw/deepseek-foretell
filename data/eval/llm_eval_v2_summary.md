# Foretell LLM 三智能体评估 v2 — 汇总报告

**生成时间**：2026-06-28（Supervisor 修正版）  
**评估范围**：P0 十案（A08/A17/B01/B09/E05/G01/G07/X05/X06/X12）  
**方法论**：SQL基准优先 + 工具对照 + 独立审核（LLM三智能体）

---

## ⚠️ 重要修正说明：打分逻辑矛盾

**v2 子智能体产出的 pass/fail 和评分存在系统性错误**，需在此修正后作为最终结论使用。

**错误模式**：Agent 3（审核智能体）将 `correctness` 维度的评分对象混淆了：
- **实际评分的是**：Agent 2 探索过程的质量（诊断准确、推理扎实、SQL基准验证严谨）
- **应该评分的是**：Foretell 生产环境按当前代码回答用户时，答案是否正确

这两者是**反相关**的——Agent 2 找到的bug越严重，说明生产环境答题质量越差，`correctness` 应该越低，而非因为"诊断做得好"就给高分。

**证据**：
- B09 correctness=5，理由是"SQL基准与DB数据完全一致，工具gap诊断准确"——但该case的工具实际在生产环境对`series_game`参数静默返回空，用户问G7拿不到任何有效数据
- E05 correctness=5，理由是"合成ID假命中诊断准确"——但该case的JOIN逻辑在生产环境会让用户拿到完全错误的赔率数据（2009/2019年历史比赛）
- A08/A17/X05 correctness=5，但这三个case都有同一个P1 tool_logic_gap：`direction=upcoming`返回2004-2006历史数据

**修正原则**：`correctness` 应反映"如果Foretell今天在生产环境用这套工具回答用户，数据对不对"。

---

## 一、修正后的 Pass/Fail 总结

| Case | 原评分 | 原结论 | **修正后结论** | 核心依据 |
|------|--------|--------|----------------|---------|
| A08 | 4.95 | pass | **条件pass** | 3个P1 tool_logic_gap（upcoming方向语义反转+league_id过滤失效），Agent靠SQL workaround绕过工具bug才拿到正确答案；生产环境若LLM直信工具则fail |
| A17 | 5.0 | pass | **条件pass** | 同A08的工具bug在法国队重现（A08 fix后A17自动修复），探索绕过但生产环境脆弱 |
| B01 | 4.95 | pass | **pass** | 无P1级gap，工具与SQL基准一致，P3级问题不影响核心答题质量 |
| B09 | 4.5 | pass | **FAIL** | P1 tool_logic_gap：`series_game`参数被静默忽略（mysql_client.py 320-321行`return []`），生产环境G7查询工具实际从未执行，用户拿不到任何G7数据 |
| E05 | 4.6 | pass | **FAIL** | P1 tool_logic_gap：lottery_zc_match.match_id是合成ID非真实外键，JOIN产生假命中（14/14全是2009/2019历史比赛），生产环境用户拿到完全错误的赔率/近况数据 |
| G01 | 4.35 | pass | **条件pass** | P1 tool_logic_gap：resolve_lottery_match不带date参数静默返回错误场次，生产LLM若不传date会整条应答错位；Agent通过多轮探索找到正确路径，但依赖不稳定workaround |
| G07 | 4.3 | pass | **条件pass** | P2级问题为主（sell_status过滤缺失、team名称映射不全），无P1；生产环境会推荐已停售场次，但不会给出完全错误的数据 |
| X05 | 4.6 | pass | **条件pass** | 同A08/A17的P1 tool_logic_gap，护栏类问题（"今天有X比赛吗"）直接受`direction=upcoming`语义反转影响 |
| X06 | 4.6 | pass | **pass** | 无P1级gap，P2路由问题有workaround（双向查询），核心实体解析可用 |
| X12 | 4.75 | pass | **条件pass** | P1 tool_logic_gap：resolve_match无swap fallback，用户主客颠倒时ENTITY_NOT_FOUND，P2多轮继承依赖LLM自维护 |

**修正后统计**：
- FAIL（生产环境核心功能损坏）：**2/10**（B09、E05）
- 条件pass（生产环境有workaround但脆弱）：**5/10**（A08、A17、G01、X05、X12）
- pass（生产质量可接受）：**3/10**（B01、G07、X06）

---

## 二、Gap 清单（按优先级排序）

### P1 — 生产环境现在就在用错误逻辑（必须立即修复）

| # | Gap类型 | 涉及Case | 问题描述 | 代码定位 |
|---|---------|---------|---------|---------|
| 1 | tool_logic_gap | A08/A17/X05/X12共4案 | `get_team_schedule(direction=upcoming)` 语义反转：返回2004-2006历史升序，而非未来赛事；`league_id`参数被静默忽略 | `foretell/tools/schedule.py` + `foretell/tools/crazy_sports/client.py` `get_team_schedule` |
| 2 | tool_logic_gap | B09 | `resolve_match` 暴露`series_game`参数但`mysql_client.py`第320-321行`if series_game is not None: return []`直接返回空，G7查询静默失效 | `foretell/tools/crazy_sports/mysql_client.py` 第320-321行 |
| 3 | tool_logic_gap | E05 | `lottery_zc_match.match_id`是合成ID（`issue*10+entry_num`），非`football_match.id`真实外键，JOIN产生假命中 | `foretell/tools/crazy_sports/mysql_client.py` `_row_lottery_entry` + `get_lottery_schedule` |
| 4 | tool_logic_gap | G01 | `resolve_lottery_match`不带`date`参数时静默返回最新期同名code场次，无ambiguous提示 | `foretell/tools/entity.py` `resolve_lottery_match` |
| 5 | tool_logic_gap | X12 | `resolve_match`无home/away swap fallback，主客颠倒时ENTITY_NOT_FOUND | `foretell/tools/crazy_sports/mysql_client.py` `resolve_match` |

### P1 — 工具完全缺失（核心业务场景不可用）

| # | Gap类型 | 涉及Case | 问题描述 |
|---|---------|---------|---------|
| 6 | implementation_gap | B09 | 篮球工具集完全缺失：`resolve_match`/`get_h2h`/`get_recent_form`均只查`football_*`表，NBA系列赛场景无法服务 |

### P2 — 功能降级（有workaround但增加LLM负担/易出错）

| # | Gap类型 | 涉及Case | 问题描述 |
|---|---------|---------|---------|
| 7 | context_gap | A08/X12 | 无checkpointer机制，多轮上下文继承完全依赖LLM自维护 |
| 8 | routing_gap | A08/A17 | Skill层未固化"国家队+时间窗"问题的默认赛事推断规则 |
| 9 | routing_gap | X06 | entity resolution未强制双向查询（用户表述主客可能与DB相反） |
| 10 | parameter_gap | G01 | `resolve_lottery_match` `date`参数docstring与实际语义不符（开售日 vs match_time日期） |
| 11 | tool_logic_gap | G07 | `get_lottery_schedule`不过滤`sell_status`，返回已停售场次 |
| 12 | implementation_gap | G07 | 北单队名与`football_team.name_zh`部分不匹配，低级别联赛覆盖不全 |
| 13 | implementation_gap | E05 | `get_lottery_schedule`返回不含`status_id`字段，需额外JOIN才能做两阶段初筛 |

### P3 — 轻微（不影响核心，可后续优化）

| # | Gap类型 | 涉及Case | 问题描述 |
|---|---------|---------|---------|
| 14 | data_gap | A17 | 7/1淘汰赛部分竞彩信息未完整录入（赛事信息有但竞彩不全） |
| 15 | tool_logic_gap | B01 | 工具签名参数对照细节（supplement_summary结论已修正，非真正gap） |
| 16 | implementation_gap | X06 | resolve_match结果缺少赛事等级/轮次字段，需LLM自行从候选集推断 |

---

## 三、Phase 2 行动计划（修正版决策树）

基于修正后的gap结论，**按紧急程度排序**：

### Phase 2a-1：紧急代码修复（P1 tool_logic_gap，有明确代码行号）

**优先级最高**，因为这些bug在生产环境现在就在造成错误回答：

1. **修复`get_team_schedule`**（影响A08/A17/X05，3个case）
   - `direction=upcoming`：加`WHERE match_time > UNIX_TIMESTAMP(NOW()) AND status_id IN (1,9,13)`
   - `league_id`过滤：strip前缀后加`WHERE competition_id=?`，在所有direction生效
   - 文件：`foretell/tools/schedule.py` + `foretell/tools/crazy_sports/client.py`

2. **修复`mysql_client.py`第320-321行**（影响B09）
   - 删除`if series_game is not None: return []`
   - 实现：查`basketball_bracket_match_up`找对阵 → 解析`match_ids`第N个 → 查`basketball_match`

3. **修复`lottery_zc_match.match_id` JOIN逻辑**（影响E05，P1最严重）
   - `_row_lottery_entry`：用home/away名称+match_time日期JOIN `football_match`+`football_team`反查真实`football_match.id`
   - 文件：`foretell/tools/crazy_sports/mysql_client.py`

4. **修复`resolve_lottery_match`无date时的歧义处理**（影响G01）
   - 同名code跨多期时必须返回ambiguous+候选列表，禁止静默取最新

5. **修复`resolve_match`增加swap fallback**（影响X12）
   - home/away 0命中时自动反向再查，命中时在meta标记`orientation_swapped=true`

### Phase 2a-2：篮球工具集实现（P1 implementation_gap）

B09发现篮球查询场景完全无工具支撑（`basketball_bracket_match_up`/`basketball_match`有数据但没工具）。需新增：
- `resolve_basketball_team`（查`basketball_team`表）
- `resolve_basketball_match`（查`basketball_match`+`basketball_bracket_match_up`）
- `get_basketball_h2h`
复用现有envelope/status_code体系。

### Phase 2a-3：checkpointer机制（P2 context_gap）

G01/G07/X12/A08多案均标记`context_gap`，影响所有多轮追问场景（G类约20种题型）。建议评估引入`langgraph MemorySaver`或`SqliteSaver`作为轻量checkpointer，持久化`{team_id, competition_id, time_window}`跨轮继承。工作量需单独技术评估。

### Phase 2b：扩展评估（待2a完成后）

修复完成后，将评估范围从P0十案扩展到全120类型。B09/E05的P1修复会影响B类（竞彩分析）/E类（批量筛选）所有题型，应在修复后统一验证。

---

## 四、关键SQL验证锚点（供修复时参考）

v2 Agent 2产出的`path_attempts_v2/`中包含每个case的验证SQL和真实ID锚点：

| Case | 关键锚点 |
|------|---------|
| A08 | match_id=4460934，哥伦比亚主vs葡萄牙客，competition_id=1 |
| B09 | basketball_match id=3921754（马刺vsOKC G7），basketball_bracket_match_up id=922432 |
| E05 | MAX(issue)=26089，真实match_id区间4459718~4459732（14场全status_id=1） |
| G01 | issue=260428，巴黎vs拜仁，lottery_id待从lottery_jczq_odds验证 |
| X12 | match_id=4460928，挪威主vs法国客，2026-06-27 |

详细SQL见对应`path_attempts_v2/*.yaml`的`evidence_ref`字段。

---

## 五、与v1结论的差异对比

| | v1（已废弃） | v2修正后 |
|---|------------|---------|
| pass/fail | 5pass/5fail | 3pass/5条件pass/2fail |
| B01判定 | fail（data_gap误判） | **pass**（supplement已纠正，工具正常） |
| B09判定 | fail（笼统） | **fail**（精确到mysql_client.py 320-321行） |
| E05判定 | fail | **fail**（合成ID外键设计缺陷，比v1定位更准确） |
| G01判定 | fail | **条件pass**（工具有bug但有可靠workaround路径） |
| A08/A17判定 | pass | **条件pass**（发现3个新P1 tool_logic_gap） |
| 新发现 | — | `direction=upcoming`语义反转（影响4个case）；合成ID假命中；series_game静默失效 |
