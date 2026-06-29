# Foretell LLM Eval v2 — B+C 场景批次汇总(24 类型)

执行时间:2026-06-29
方法论:**LLM 自主判断**(沿用 A/X 方法论)。path-explorer-agent 实调 foretell tools 探索路径。
本批次覆盖:B01-B16(深度分析16) + C01-C08(赛后复盘8),分 7 批派发。

## 一、总表

### B 深度分析(16个)

| type_id | 名称 | 分类 | 关键发现 |
|---|---|---|---|
| B01 | 竞彩模板分析 | ✅ | 6/6 atomic,深度工具全 OK(lineup/injury/intel/stats/trend/kelly),resolve_lottery_match routing bug 有 fallback |
| B02 | 竞彩篮球模板 | ⚠️ | get_team_schedule 跨运动碰撞,lottery match_id=null,NBA 休赛 data_gap |
| B03 | 对阵加日期分析 | ✅ | 4/4 atomic,简称规范化 fallback(町田泽维→町田泽维亚) |
| B04 | 对阵无日期分析 | ❌ | resolve_match 无 date 时 LIMIT 10 使女足/青年占满窗口,男子 A 级被截断 |
| B05 | 谁会赢 | ✅ | 4/4 atomic,工具链全 OK,国际赛用 fifa_ranking |
| B06 | 全面深度分析 | ⚠️ | "今天竞彩001"DB 不存在(data_gap),但 16 维度深度链全 OK |
| B07 | 自定义模板 | ✅ | 4/4 atomic,七段式 12 类工具全 OK |
| B08 | 篮球五段分析 | ❌ | deep 工具跨运动 match_id 碰撞(NBA match_id 返回足球数据),污染分析 |
| B09 | 系列赛G7 | ⚠️ | series_game bug 修复生效✅,但 resolve_match 不支持 basketball_match + series_game 未作 SQL 过滤 |
| B10 | 淘汰赛排名不适用 | ⚠️ | get_standings 对淘汰赛不降级,缺"排名不适用"语义判定 |
| B11 | 盘口不足跳过 | ✅ | 4/4 atomic,SKIP_MATCH 降级语义完整 |
| B12 | 换线重定价 | ✅ | 4/4 atomic,odds 三档对比+50 变化点+kelly 价值面 |
| B13 | 伤病结合分析 | ✅ | 4/4 atomic,injury+lineup+squad 全 OK(lineup home/away 颠倒瑕疵) |
| B14 | 进球数深度 | ✅ | 4/4 atomic,11 工具全 OK,over_under+goals_lost_rate+incidents |
| B15 | 半全场分析 | ✅ | 4/4 atomic,half_stats 三 scope 自洽+half_odds 15 条+score_breakdown |
| B16 | 实力对比 | ✅ | 4/4 atomic,fifa_ranking+team_honors+coach+half_stats 全维度覆盖 |

### C 赛后复盘(8个)

| type_id | 名称 | 分类 | 关键发现 |
|---|---|---|---|
| C01 | 昨天比赛复盘 | ✅ | 2/2 atomic,复盘六链全 OK(atomic 文案与 type_name 不符) |
| C02 | 上周比赛复盘 | ⚠️ | 工具层打通,但用户前提与 DB 不符(英超休赛),应主动澄清 |
| C03 | 对阵复盘 | ✅ | 2/2 atomic,4场×6工具=24调用全 OK,日期口径 fallback(6/18→6/19) |
| C04 | 竞彩编号复盘 | ✅ | 5 atomic,resolve_lottery_match routing bug 有 fallback,全维度 OK |
| C05 | 篮球复盘 | ⚠️ | type_name 标篮球但 scenario 实际足球,按足球路径 17 工具全 OK |
| C06 | 焦点战回顾 | ✅ | 2/2 atomic,7 工具一次通过无 fallback |
| C07 | 近期战绩复盘 | ❌ | cross_sport_data_collision:篮球 team_id 传入足球工具静默返回足球数据 |
| C08 | 欧冠复盘 | ✅ | 2/2 atomic,六链全 OK,fallback 生效(atomic 文案与 type_name 不符) |

**分类统计**:
- ✅ 找到可行路径:**15 个**(B01,B03,B05,B07,B11,B12,B13,B14,B15,B16,C01,C03,C04,C06,C08)
- ⚠️ 找到路径但有隐患:**6 个**(B02,B06,B09,B10,C02,C05)
- ❌ 穷尽探索后确认无解:**3 个**(B04,B08,C07)

## 二、修复的 bug(B+C 批次期间)
无新 bug 修复(Phase 2 已修复的 bug 在本批次验证生效:series_game bug B09✅、odds_trend 分区路由 B01✅、stub 实现 B01/B05/B07 等全 OK)。

## 三、待修复的 gap(P3 候选,跑完全部 120 场景后统一排优先级)

### 高优先级(安全隐患/架构问题)
| type_id | gap 类型 | 描述 | 修复路径 |
|---|---|---|---|
| B08/C07 ❌ | cross_sport_data_collision | 篮球 team_id/match_id 传入足球 deep 工具(get_recent_form/get_team_schedule/get_team_season_stats/get_injury_report/get_match_team_stats)静默返回足球数据,false positive | 新增篮球版本工具,或现有工具加 sport 参数 + SQL 路由;短期守轨:sport 不匹配返回 DATA_MISSING |
| B09 ⚠️ | implementation_gap | resolve_match 不支持 basketball_match + series_game 未作 SQL 过滤 | 扩展 resolve_match 支持 basketball_match 或新增 resolve_basketball_series_match |

### 中优先级(工具语义补全)
| type_id | gap 类型 | 描述 | 修复路径 |
|---|---|---|---|
| B04 ❌ | routing_gap | resolve_match 无 date 时 LIMIT 10 使女足/青年占满窗口 | 无 date 时扩大 LIMIT 或优先国家队成年组 |
| B10 ⚠️ | implementation_gap | get_standings 对淘汰赛不降级 | 工具层增加赛事阶段感知,淘汰赛返回 NOT_APPLICABLE |
| B02 ⚠️ | implementation_gap | get_team_schedule 不支持篮球 + lottery match_id=null | 新增 get_basketball_team_schedule |

### 低优先级(数据/标注)
| type_id | gap 类型 | 描述 |
|---|---|---|
| B06/C02 ⚠️ | data_gap | 用户前提与 DB 不符(竞彩001不存在/英超休赛),LLM 应主动澄清 |
| C05 ⚠️ | 标注错误 | type_name 标篮球但 scenario 实际足球,需修正 atomic 分解 |
| C01/C08 | 标注错误 | atomic 文案与 type_name 不符,需 regenerate |

## 四、关键洞察

1. **B 场景深度分析工具链成熟**:Phase 2 重构后 16 维度深度工具(lineup/injury/intel/team_stats/player_stats/incidents/tlive/odds_trend/kelly/betfair/over_under/half_odds/half_stats/goals_lost_rate/fifa_ranking/coach)全部返回真实数据,B01/B05/B07/B11-B16 共 10 个干净通过。

2. **篮球工具层是最大盲区**:B02/B08/B09/C07 四个篮球相关 case 全部 ⚠️ 或 ❌,根因是 Phase 2 只新增了 resolve_basketball_team/league + get_basketball_standings + get_series_matchup(sport=basketball),但 deep 工具(get_recent_form/get_team_schedule/get_team_season_stats/get_injury_report/get_match_team_stats)和 resolve_match 均不支持篮球,且存在跨运动 ID/match_id 碰撞安全隐患。

3. **C07 cross_sport_data_collision 是最危险隐患**:篮球 team_id 传入足球工具返回 OK 足球数据(10155勇士→科特布斯德丙),LLM 会把足球战绩当 NBA 汇报,构成 false positive。比 DATA_MISSING 更危险,建议优先修复。

4. **resolve_lottery_match routing bug 持续出现**:B01/B04/C04/G01 均遇 issue_num 匹配 bug,但 get_lottery_schedule fallback 稳定兜底。

5. **atomic 分解标注问题**:C01/C05/C08 的 atomic 文案与 type_name 不符(模板生成问题),需 regenerate,但不影响路径探索。

## 五、产出文件
- data/eval/path_attempts/B01-B16.yaml(16 个)
- data/eval/path_attempts/C01-C08.yaml(8 个)
- data/eval/batch_BC_summary.md(本文件)
