---
name: foretell-status-dictionary
description: Tool 层状态码到用户可见标注的映射。当解读工具返回结果、决定如何向用户呈现数据缺失或异常时使用。
---

# 状态码字典

Tool 层返回统一 envelope，`code` 字段由**工具判定**，LLM **不得猜测**状态。

## 状态码表（见设计 Spec §8.3）

| code | 用户可见标注 | 行为 |
|------|-------------|------|
| `OK` | （正常分析） | 全权重使用数据 |
| `DATA_MISSING` | 数据不足 | 跳过该细项，不编造 |
| `NOT_APPLICABLE` | 不适用 + 原因 | 提供替代信息或说明原因 |
| `SKIP_MATCH` | 盘口数据不足，建议跳过此场 | 欧赔+亚盘均缺时使用 |
| `ENTITY_NOT_FOUND` | 未找到比赛/实体 | 可触发网络搜索兜底（最多 1 次） |
| `PARTIAL` | 按维度分别标注 | 降权使用，标注缺失维度 |

## 使用规则

1. 读取 envelope 中的 `code`，按上表决定输出策略
2. `DATA_MISSING` / `PARTIAL`：诚实说明缺口，不填充假数据
3. `ENTITY_NOT_FOUND`：告知未找到，可建议用户核对队名或日期
4. `NOT_APPLICABLE`：说明不适用原因（如指定 G7 不存在）
5. `SKIP_MATCH`：建议用户跳过该场，不强行分析

## 禁止行为

- 忽略 `code` 直接编造比分、赔率或赛果
- 将 `ENTITY_NOT_FOUND` 当作「数据不足」模糊带过
- 向用户暴露 envelope JSON 或内部字段名

## DB 字段状态码(对照纳米文档)

工具返回的 DB 字段状态码必须按以下枚举解读,不得猜测。权威来源:`data/eval/nami_docs/status_codes_2002.md`(足球)、`status_codes_2003.md`(篮球)、`data/eval/nami_field_map_full.yaml`。

### football_match.status_id(足球比赛状态)

| code | 含义 | 工具行为 |
|------|------|----------|
| 0 | 比赛异常(腰斩/取消等,建议隐藏) | 隐藏,不向用户呈现 |
| 1 | 未开赛 | 显示赛程,无比分 |
| 2 | 上半场 | 显示进行中 + 当前比分 |
| 3 | 中场 | 显示进行中 + 半场比分 |
| 4 | 下半场 | 显示进行中 + 当前比分 |
| 5 | 加时赛 | 显示进行中 + 加时标注 |
| 7 | 点球决战 | 显示进行中 + 点球标注 |
| 8 | 完场 | 显示最终比分 + 赛果 |
| 9 | 推迟 | 标注推迟,显示原定时间 |
| 10 | 中断 | 标注中断 |
| 11 | 腰斩 | 标注腰斩 |
| 12 | 取消 | 标注取消 |
| 13 | 待定 | 标注待定 |

常用过滤:进行中 `IN (2,3,4,5,7)` / 未开赛 `=1` / 已完赛 `=8`。

### basketball_match.status_id(篮球比赛状态,与足球不同!)

| code | 含义 |
|------|------|
| 0 | 比赛异常 |
| 1 | 未开赛 |
| 2 | 第一节 |
| 3 | 第一节完 |
| 4 | 第二节 |
| 5 | 第二节完 |
| 6 | 第三节 |
| 7 | 第三节完 |
| 8 | 第四节(**非完场!**) |
| 9 | 加时赛 |
| 10 | 完场 |
| 11 | 中断 |
| 12 | 取消 |
| 13 | 延期 |
| 14 | 腰斩 |
| 15 | 待定 |

**高危**:篮球 `status_id=8` 是第四节,足球 `status_id=8` 是完场。重写时不得共用一套状态码。

### basketball_match.kind(比赛类型)

| code | 含义 |
|------|------|
| 0 | 无 |
| 1 | 常规赛 |
| 2 | 季后赛 |
| 3 | 季前赛 |
| 4 | 全明星 |
| 5 | 杯赛 |
| 6 | 附加赛 |

### football_team_injury.type(伤停类型)

| code | 含义 |
|------|------|
| 0 | 未知 |
| 1 | 受伤 |
| 2 | 停赛 |
| 3 | 出战成疑 |

### football_match_incidents.type(技术统计/事件类型,足球)

高频值:`1进球 / 2角球 / 3黄牌 / 4红牌 / 9换人 / 17乌龙球 / 18助攻 / 21射正 / 22射偏 / 25控球率`。完整枚举见 `data/eval/nami_docs/status_codes_2002.md` 技术统计表。

### football_competition.type(赛事类型,决定积分榜 schema)

| code | 含义 | standings 输出 |
|------|------|----------------|
| 1 | 联赛 | 单表积分榜 |
| 2 | 杯赛 | 多组 + 第3名榜 + promotion_id,淘汰赛阶段排名不适用 |
| 3 | 友谊赛 | 无积分榜 |

### bracket_match_up.type_id(系列赛赛制)

| code | 含义 |
|------|------|
| 1 | 单场决胜 |
| 8 | 三局两胜 |
| 9 | 五局三胜 |
| 10 | 七局四胜(G7 = type_id=10 且 home_score+away_score=6) |

### lottery_jczq_odds.sell_status(竞彩销售状态)

| code | 含义 |
|------|------|
| 0 | 未开售 |
| 1 | 仅过关 |
| 2 | 单关和过关 |
| 3 | 停售 |

### 指数公司 ID(高频)

`2 BET365 / 3 皇冠 / 5 立博 / 7 澳彩 / 9 威廉希尔 / 10 易胜博 / 11 韦德 / 15 利记 / 16 盈禾 / 19 竞彩官方 / 22 平博 / 136 马会`。完整枚举见 `data/eval/nami_docs/status_codes_2002.md` 指数公司ID表。

## 跨运动 ID 碰撞警示(P0)

`football_team.id` 与 `basketball_team.id` 共享同一整数空间,数值可碰撞(如 10155 既是篮球卡塔尔又是足球索菲亚火车头)。`football_match.id` 与 `basketball_match.id` 同理。

**强制规则**:所有 deep/stats/odds 工具必须支持 `sport` 参数,不匹配时 fail-closed 返回 `DATA_MISSING`,禁止静默命中足球数据。详见 `data/eval/nami_field_map_full.yaml` 的 `cross_sport_id_collision` 条目。
