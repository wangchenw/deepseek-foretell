# Foretell 工具层重写粒度方案(3 候选对比 + 推荐)

> 输入:阶段 0 nami_field_map_full.yaml(字段语义)+ 阶段 1 tool_requirements_by_scenario.yaml(9 大类需求)
> 决策:用户在 3 方案中拍板,作为阶段 3 重写的依据

## 一、三方案对比


| 维度       | 方案 A 粗粒度  | 方案 B 细粒度  | 方案 C 混合粒度(推荐)  |
| -------- | --------- | --------- | -------------- |
| 工具数      | ~15-20    | ~60-80    | ~30-40         |
| 切分依据     | 场景聚合点     | 数据维度      | 场景聚合点 + 数据维度分层 |
| LLM 选型负担 | 低(少选)     | 高(多选)     | 中(分层选)         |
| 参数复杂度    | 高(多参数多维度) | 低(单一职责)   | 分层(基础低/聚合高)    |
| 返回大小     | 大(聚合)     | 小(单维度)    | 分层(基础小/聚合大)    |
| 编排复杂度    | 低(一次拿全)   | 高(多工具串联)  | 中(聚合场景少串联)     |
| 调试难度     | 高(出错难定位)  | 低(单工具单职责) | 中(分层定位)        |
| 灵活性      | 差(场景固定)   | 好(任意组合)   | 中(聚合点固定+基础灵活)  |
| 上下文成本    | 低(少工具描述)  | 高(多工具描述)  | 中(30-40 描述)    |




## 二、推荐:方案 C 混合粒度



### 设计原则

1. **三层结构**:基础层(细粒度,单维度查询)+ 聚合层(粗粒度,场景级聚合)+ 护栏层(sport 校验/状态字典)
2. **sport 一等参数**:所有 deep/stats/odds 工具加 sport 参数,fail-closed 杜绝跨运动碰撞
3. **ID 语义显式化**:返回区分 football_match_id / lottery_official_id / lottery_entry_id
4. **解析按数据源分支**:lottery 101/201 CSV,301/404 JSON
5. **赛制感知**:standings 按 competition.type 分支输出
6. **字段对照权威表**:每个工具实现对照 nami_field_map_full.yaml



### 工具清单(共 35 个)



#### 基础层:实体解析(6 个,所有场景入口)


| 工具                        | 职责                          | 关键参数                                 | sport 参数                  |
| ------------------------- | --------------------------- | ------------------------------------ | ------------------------- |
| resolve_team              | 按名/别名查球队                    | name, aliases, national, gender, age | sport=football/basketball |
| resolve_league            | 按名/别名查赛事                    | name, aliases                        | sport                     |
| resolve_match             | 按主客+日期查比赛                   | home, away, date, national, gender   | sport                     |
| resolve_lottery_match     | 按彩种+编码+期号查彩票场次              | play_type, code, issue, date         | — (lottery 自带隔离)          |
| resolve_lottery_entry     | 解析彩票场次为真实 football_match_id | play_type, issue, issue_num          | —                         |
| resolve_basketball_series | 篮球系列赛定位(G7)                 | home, away, series_type              | sport=basketball          |




#### 基础层:赛程查询(4 个)


| 工具                   | 职责       | 关键参数                                                  |
| -------------------- | -------- | ----------------------------------------------------- |
| get_schedule_by_date | 按日期查赛程   | date, sport, league_preset, tier, status_in           |
| get_team_schedule    | 按球队查赛程   | team_id, sport, direction(recent/upcoming/all), limit |
| get_lottery_schedule | 按彩种查彩票赛程 | play_type, date, period                               |
| get_live_matches     | 在玩列表(新增) | sport, league_id                                      |




#### 基础层:赔率查询(7 个,聚合盘口快照)


| 工具                    | 职责                               | 关键参数                                                           |
| --------------------- | -------------------------------- | -------------------------------------------------------------- |
| get_odds_snapshot     | 欧赔+亚盘聚合快照(替代旧 5 工具)              | match_id, sport, companies, limit                              |
| get_odds_trend        | 赔率走势时序(欧赔+亚盘)                    | match_id, sport, kind(european/asian/both), limit              |
| get_special_odds      | 扩展盘口(大小球/半场/角球/百欧/官让)            | match_id, sport, kind(over_under/half/corner/hundred/official) |
| get_kelly             | 凯利指数                             | match_id, sport                                                |
| get_betfair           | 必发指数                             | match_id, sport                                                |
| get_same_odds_history | 同赔历史                             | match_id, sport                                                |
| get_lottery_odds      | 彩票玩法赔率(spf/rq/bf/jq/bqc 按彩种分支解析) | play_type, issue, issue_num, kinds                             |




#### 基础层:统计与深度(8 个)


| 工具                    | 职责                                 | 关键参数                                      |
| --------------------- | ---------------------------------- | ----------------------------------------- |
| get_standings         | 积分榜(赛制感知+season 智能选择+promotion_id) | league_id, sport, season_id, stage, scope |
| get_team_season_stats | 球队赛季统计                             | team_id, sport, season_id                 |
| get_recent_form       | 近期战绩(支持 before_date)               | team_id, sport, limit, before_date        |
| get_h2h               | 交锋历史                               | home_team_id, away_team_id, sport, limit  |
| get_match_lineup      | 阵容                                 | match_id, sport                           |
| get_injury_report     | 伤停                                 | team_id, sport                            |
| get_intel_tags        | 情报                                 | match_id, sport                           |
| get_match_stats       | 比赛统计(球队+球员聚合)                      | match_id, sport, scope(full/half)         |




#### 基础层:比赛详情(4 个)


| 工具                  | 职责                  | 关键参数             |
| ------------------- | ------------------- | ---------------- |
| get_match_result    | 比赛结果(比分+事件聚合)       | match_id, sport  |
| get_match_incidents | 比赛事件(进球/红黄牌/换人)     | match_id, sport  |
| get_match_tlive     | 文字直播                | match_id, sport  |
| get_series_matchup  | 系列赛对阵(完整 match_ids) | series_id, sport |




#### 基础层:实体资料(4 个)


| 工具                   | 职责                   | 关键参数                                       |
| -------------------- | -------------------- | ------------------------------------------ |
| get_player_profile   | 球员资料(含身价/转会/荣誉)      | player_id, sport, sections                 |
| get_team_info        | 球队资料(含荣誉/教练/场馆)      | team_id, sport, sections                   |
| get_competition_info | 赛事资料(含赛季/阶段/积分榜类型)   | league_id, sport                           |
| get_ranking          | 排名(FIFA/俱乐部/FIBA 聚合) | type(fifa_men/fifa_women/club/fiba), sport |




#### 聚合层:场景级聚合(4 个,高频场景一站式)


| 工具                 | 职责       | 触发场景          | 聚合内容                                                                                               |
| ------------------ | -------- | ------------- | -------------------------------------------------------------------------------------------------- |
| get_match_analysis | 单场深度分析聚合 | B/C/D/G 类深度模板 | resolve + lineup + injury + intel + stats + odds_snapshot + odds_trend + kelly + recent_form + h2h |
| get_lottery_batch  | 彩票批次聚合   | D/E 类批量串关     | get_lottery_schedule + 批量 resolve_lottery_entry + 批量 get_lottery_odds + 批量 get_match_analysis(可选)  |
| get_standings_full | 积分榜全量聚合  | H 类语义精度       | get_standings + promotion_id/football_promotions + 剩余轮次 + 资格规则                                     |
| get_match_review   | 比赛复盘聚合   | C 类赛后复盘       | get_match_result + get_match_incidents + get_match_stats + get_match_tlive + 赔率回顾                  |




#### 护栏层(2 个)


| 工具               | 职责                                                                                            |
| ---------------- | --------------------------------------------------------------------------------------------- |
| internet_search  | 网络兜底(保留)                                                                                      |
| _sport_guard(内部) | sport 校验中间件,不暴露给 LLM,所有 deep/stats/odds 工具调用前自动校验 team_id/match_id 属于正确 sport,不匹配 fail-closed |




### 与现有 53 工具的对比


| 维度           | 现有                                   | 重写后                                               |
| ------------ | ------------------------------------ | ------------------------------------------------- |
| 工具数          | 53                                   | 35                                                |
| 足球/篮球分裂      | 3 对(resolve_team/basketball_team 等)  | 统一 sport 参数                                       |
| 盘口工具碎片       | 10 个(odds.py 5 + extra.py 5)         | 7 个(按 kind 参数聚合)                                  |
| 资料工具碎片       | coach/referee/venue/market_value 等独立 | 聚合进 get_player_profile/get_team_info(sections 参数) |
| lottery 解析   | 统一 CSV 切(北单 JSON 被切碎)                | 按彩种分支(101 CSV / 301 JSON)                         |
| ID 语义        | match_id 一词三义                        | 显式区分 football_match_id/lottery_official_id        |
| sport 路由     | 无(跨运动碰撞)                             | 一等参数 + fail-closed                                |
| standings 赛制 | 单表联赛模型                               | 按 competition.type 分支 + promotion_id              |
| 场景聚合         | 无(逐工具串联)                             | 4 个聚合工具(B/C/D/E/H 高频场景)                           |




## 三、聚合工具的取舍说明

聚合层是方案 C 的关键创新,但也是争议点:

**支持聚合的理由**:

- B 类深度模板常调 11-16 个工具,LLM 编排负担重,聚合后一次拿全
- D/E 类批量串关 14 场,逐场调 137 次,聚合后批量返回
- H 类语义精度需积分榜+资格规则+剩余轮次三源合成,聚合后开箱即用

**反对聚合的理由**:

- 聚合工具返回大,LLM 可能只需要其中一部分
- 聚合点固定,新场景不命中时仍需回基础层
- 调试时出错难定位是哪个子调用

**折中**:聚合工具支持 `sections` 参数(类似 get_player_profile),LLM 可指定只取部分维度,默认全取。例如 `get_match_analysis(match_id, sections=[lineup,odds_snapshot])` 只取阵容+盘口。

## 四、不聚合保留细粒度的部分

以下维度不聚合,保持细粒度(低频或独立性强):

- get_match_tlive(文字直播,实时流,独立)
- get_match_incidents(事件流,独立)
- get_series_matchup(系列赛,独立)
- get_same_odds_history(同赔历史,低频)
- get_ranking(排名,低频)
- internet_search(网络兜底,独立)



## 五、决策点

需用户拍板:

1. 选哪个方案(A 粗 / B 细 / C 混合推荐)
2. 聚合层是否保留(方案 C 的争议点)
3. 聚合工具是否支持 sections 参数(折中方案)

