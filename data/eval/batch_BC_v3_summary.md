# v3 eval 批次汇总 — B+C

- 验证日期: 2026-06-30
- 范围: B 深度分析 + C 赛后复盘(v2 ⚠️ 子集)

| type_id | 名称 | v2 | v3 | 变化 |
|---------|------|-----|-----|------|
| B02 | 竞彩篮球模板 | ⚠️ | ✅ | ↑ lottery 201 match_id 回填 + 篮球 deep sport 路由全打通 |
| B04 | 对阵无日期分析 | ⚠️ | ✅ | ↑ resolve_match national+exclude_youth,男子国家队 A 级置顶 |
| B06 | 全面深度分析 | ⚠️ | ✅ | ↑ 篮球多工具组合全 OK,8 类无数据短路 DATA_MISSING+reason |
| B08 | 篮球五段分析 | ⚠️ | ⚠️ | — DATA_MISSING 提示明确化,但 basketball_match_team_data 表未路由 |
| B09 | 系列赛G7 | ⚠️ | ⚠️ | — series_matchup 返数据,但 G7 具体场次未细查 |
| B10 | 淘汰赛排名不适用 | ⚠️ | ✅ | ↑ 杯赛 competition_type=2 感知,不套联赛积分榜逻辑 |
| C02 | 上周比赛复盘 | ⚠️ | ✅ | ↑ 篮球复盘路径(h2h+schedule+recent_form) sport=basketball 全通 |
| C07 | 近期战绩复盘 | ⚠️ | ✅ | ↑ get_recent_form sport=basketball 走篮球表,无 cross_sport 碰撞 |

**批次结论**: 6/8 升档 ✅,2/8 残留 ⚠️(B08 篮球 team_data 表未路由/B09 G7 未细查)。新发现 P6(h2h 篮球字段语义错位)、P7(schedule 元数据透传 bug)、P8(standings 重复行)。
