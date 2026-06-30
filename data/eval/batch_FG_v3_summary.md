# v3 eval 批次汇总 — F+G

- 验证日期: 2026-06-30
- 范围: F 赔率查询 + G 多轮追问(v2 ⚠️ 子集)

| type_id | 名称 | v2 | v3 | 变化 |
|---------|------|-----|-----|------|
| F03 | 变动最大 | ⚠️ | ✅ | ↑ get_odds_trend sport=basketball 走年分区表,2-way 赔率不伪命中足球 |
| G03 | 各比分概率 | ⚠️ | ✅ | ↑ resolve_lottery_match 合成 ID 分离 + 各比分概率工具链全通 |
| G05 | 继续追问 | ⚠️ | ✅ | ↑ 合成 ID 分离 + match_incidents/team_stats/recent_form OK |
| G07 | 优化方案 | ⚠️ | ✅ | ↑ 北单 bf/spf/jq/bqc/sxp 全结构化 + 合成 ID 分离 |
| G08 | 同样逻辑(NBA 深度) | ⚠️ | ⚠️ | — 4 维度升 OK,残留 team_season_stats 表名 bug(P5) |

**批次结论**: 4/5 升档 ✅,1/5 残留 ⚠️(G08 P5 表名错+效率表未路由)。新发现 P5(get_team_season_stats 篮球短路 reason 表名错,实际 basketball_competition_team_stats 存在含效率字段)。
