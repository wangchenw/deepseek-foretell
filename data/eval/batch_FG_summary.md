# Foretell LLM Eval v2 — F+G 场景批次汇总(30 类型)

执行时间:2026-06-29
方法论:**LLM 自主判断**(沿用前批次)。path-explorer-agent 实调 foretell tools 探索路径。
本批次覆盖:F01-F10(赔率查询10) + G01-G20(多轮追问20),分 6 波并发派发。
**G 场景为多轮追问**(entity_entry=context),含 maintain_context/delegate_subagent 编排类 atomic,需区分工具层 vs agent 编排层(agent_layer_covered)。

## 一、总表

### F 赔率查询(10个)

| type_id | 名称 | 分类 | 关键发现 |
|---|---|---|---|
| F01 | 赔率对比 | ✅ | get_odds_snapshot 返回5欧赔+5亚盘三段结构化;LIMIT 5 截断(DB实有19欧/17亚)completeness瑕疵非阻塞 |
| F02 | 赔率走势 | ✅ | get_odds_trend 50时点+odd-month分区路由正常;队名别名"艾阿利"→"麦纳麦国民"routing_gap 2轮可解 |
| F03 | 变动最大 | ⚠️ | 足球路径通;**篮球分支implementation_gap**(get_odds_trend硬编码football表对篮球DATA_MISSING,SQL查basketball_odds_europe_change_2026实有2436点);无批量odds_trend入口需逐场~137次 |
| F04 | 凯利指数 | ✅ | get_kelly返回5家odds+implied_prob+kelly三元组;Al-Ahli高歧义跨联赛同名需competition_id过滤 |
| F05 | 赔率时间线 | ✅ | get_odds_trend 50时点+get_same_odds_history 10条;odd-month分区路由正常;字段已结构化 |
| F06 | 盘口解读 | ✅ | 四类盘口工具(odds_snapshot/official_handicap/over_under/odds_trend)均含initial/current/latest三态;lottery match_id=null须resolve_match二次定位 |
| F07 | 临场盘口 | ✅ | 数据路径完整;**阶段错位**(06-30比赛stage=1/16决赛,积分榜stage=小组赛);**get_standings group过滤失效+主客分列置零**,SQL直查football_points_table_team规避 |
| F08 | 现在盘口 | ✅ | 即时盘路径全通(odds_snapshot三层+over_under+odds_trend 50时序);follow_up maintain_context归agent编排层 |
| F09 | 水位方向 | ✅ | get_odds_snapshot asian含home_line/handicap/away_line三段水位结构化;**get_odds_trend缺亚盘水位维度**(仅欧赔),SQL football_odds_asian_change_YYYYMM双月分区补全(2537条) |
| F10 | 欧赔亚盘 | ✅ | get_odds_snapshot单调返回欧赔+亚盘联合快照;亚盘初盘-0.5→即时-0.25跨公司一致精确印证文案 |

### G 多轮追问(20个)

| type_id | 名称 | 分类 | 关键发现 |
|---|---|---|---|
| G01 | 比分预测追问 | ✅ | **P0标注data_gap实为routing_gap**:resolve_lottery_match裸code="004"失败,正确code="周二004"+date;lottery bf 31项比分赔率实可得;turn1数据源充分(bf+h2h+goals_lost_rate+half_stats+over_under+betfair) |
| G02 | 率先进球追问 | ✅ | 率先进球无专用工具,三源合成(goals_lost_rate 7时段+h2h half_time+incidents逐球minute/side首球凯恩17'点球);6个maintain_context归编排层 |
| G03 | 各比分概率 | ⚠️ | 无专用score_breakdown工具,bf赔率倒数归一即隐含概率矩阵;**继承G01上游data_gap**(周二004巴黎vs拜仁当前期ENTITY_NOT_FOUND)非追问能力本身缺口 |
| G04 | 上半场进球概率 | ✅ | 三源互补(goals_lost_rate 7时段赛前即有主源+half_stats p1+h2h half_time);**resolve_team("日本")只返回U系列未命中成年队**(同E10),正确team_id须取自football_match主客列 |
| G05 | 继续追问 | ⚠️ | 3 atomic全agent_layer_covered;**前序对象"今天竞彩001"DB不存在**(issue=260629仅074-076三场无001编码),follow_up数据前提缺失 |
| G06 | 复述原文 | ✅ | turn0 fallback命中(swap大阪钢巴主vs清水心跳客);**命名歧义"清水鼓动"仅匹配U23,一线队规范名"清水心跳"**;主客顺序反转swap后命中(同X12) |
| G07 | 优化方案 | ⚠️ | Phase 2后主路径全通(get_kelly/odds_trend/betfair三新维度OK);**北单bf序列化损坏bug实锤**(odds字段切JSON碎片,同D05/D08/E06);turn2跨窗口引用context_gap(需checkpointer) |
| G08 | 同样逻辑 | ❌ | turn1 NBA深度模板**implementation_gap阻断**:stats/odds工具全足球专用无篮球效率/Pace/三分%/盘口工具,player无injury接口;resolve_match湖人vs凯尔特人ENTITY_NOT_FOUND(NBA未入库,同B09) |
| G09 | 换场追问 | ✅ | 换场数据路径通畅(resolve_match球队名+date复用);**short code路由断裂同G01/E05**(resolve_lottery_match 005 ENTITY_NOT_FOUND,lottery_code"周一074"格式match_id=null);resolve_team(巴西)需national=1过滤 |
| G10 | 重新分析 | ✅ | 七大维度27工具全stub=false实现完整;**用已完赛比赛交叉验证**:未开赛DATA_MISSING是物理时序非implementation_gap(南非vs加拿大 team_stats/player_stats/half_stats/incidents全OK) |
| G11 | 用户纠正 | ✅ | 用户纠正后重新resolve到正确实体新西兰vs智利FIFA系列赛(match_id 4481509);6深度工具全OK非stub;intel_tags佐证纠正事实;从历史blocked升级pass |
| G12 | 时间窗纠正 | ✅ | 时间窗纠正成功(北京日期重调resolve_match全命中);**跨日陷阱在UTC层**(06:00/09:00早场属前日UTC但get_schedule_by_date按北京日分窗,须用北京日期);2018旧场主客反转未碰撞 |
| G13 | 进球数追问 | ✅ | 进球数深度路径全通(over_under+goals_lost_rate+h2h+odds_snapshot);**客队名消歧易错点**"维尼亚德马埃弗顿"全称未命中须resolve_team aliases跳"埃弗顿VM" |
| G14 | 半全场追问 | ✅ | bqc 9项半全场赔率结构化完整+half_odds+odds_snapshot;**resolve_lottery_match编码路由全失败同G01**,fallback get_lottery_schedule→队名→resolve_match回填;7维度5OK+2赛前合理data_gap |
| G15 | 综合分析追问 | ✅ | "吉普"音译消歧(吉普→JIPPO→基柏);三维度全可得(standings主客分列+近期SQL兜底+odds_snapshot);**get_team_season_stats未按season_id过滤误返芬兰杯**,SQL直查规避 |
| G16 | 盘口变化追问 | ✅ | 双源互补(odds_snapshot亚盘handicap三时点-1.0→-0.5→-0.25+odds_trend 50欧赔时序);**get_odds_trend只覆盖欧赔时序不含亚盘handicap时序**;用户文案"瑞典主场"与DB neutral=true中立场不符 |
| G17 | 多场比赛追问 | ✅ | 批量→单场切换验证成功(resolve_lottery_match周一076+date锁定4459719);单场深度链全覆盖;软缺口(h2h DATA_MISSING/injury空)由intel_tags叙事补偿 |
| G18 | 球员情况追问 | ✅ | 稳定路径(resolve_team→team_schedule取match_id→injury_report空伤停+squad 26大名单综合判定"均能出战");lineup临场增强(未开赛DATA_MISSING正常);resolve_team需national=1 |
| G19 | 短确认 | ✅ | turn0工具链OK;turn1短确认纯agent编排层语义处理工具层无新调用;DB场次status=finished与文案"今晚开赛"时态错配非阻塞 |
| G20 | 格式重写 | ✅ | turn0上下文真实可追溯(resolve_match命中4530473,neutral=true解释"艾阿利(中)");turn1格式重写无新数据需求纯session上下文+格式重组,3 atomic全agent_layer_covered |

**分类统计**:
- ✅ 找到可行路径:**25 个**(F01,F02,F04,F05,F06,F07,F08,F09,F10,G01,G02,G04,G06,G09,G10,G11,G12,G13,G14,G15,G16,G17,G18,G19,G20)
- ⚠️ 找到路径但有隐患:**4 个**(F03,G03,G05,G07)
- ❌ 穷尽探索后确认无解:**1 个**(G08)

## 二、新发现/再次实锤的 bug / gap

### 高优先级(再次实锤,跨批次重复出现)
| type_id | gap 类型 | 描述 | 已记入批次 |
|---|---|---|---|
| G07 | implementation_gap | **北单bf/spf序列化损坏bug**:odds字段切JSON碎片,标签完整但赔率值不可靠 | D05/D08/E06/E07(同源) |
| G08 ❌ | implementation_gap | **篮球深度工具完全缺失**:stats/odds工具全足球专用,无篮球效率/Pace/三分%/盘口工具,player无injury接口 | B02/B08/B09/C07/D07(同源) |
| F03 | implementation_gap | **get_odds_trend硬编码football表对篮球DATA_MISSING**,SQL查basketball_odds_europe_change_2026实有数据 | 新发现(篮球赔率走势) |
| F09/G16 | implementation_gap | **get_odds_trend只覆盖欧赔时序不含亚盘handicap时序**,亚盘水位时序需SQL football_odds_asian_change_YYYYMM补全 | 新发现(亚盘时序缺口) |
| F07 | implementation_gap | **get_standings group过滤失效+主客分列置零**,按组取积分榜须SQL直查football_points_table_team | B10(同源) |
| G15 | implementation_gap | **get_team_season_stats未按season_id过滤误返其他赛事**,须SQL直查football_competition_teams_stats | 新发现 |
| G01/G09/G14/E05/E06 | routing_gap | **resolve_lottery_match按竞彩编码路由全失败**:裸code ENTITY_NOT_FOUND,须带星期前缀"周二004"+date;lottery entries match_id=null须resolve_match(队名+date)回填 | 多批次重复 |

### 中优先级(实体解析)
| type_id | gap 类型 | 描述 |
|---|---|---|
| E10/G04/G09/G18 | routing_gap | **resolve_team国家队场景碰撞**:首候选常为U17/U20/U23/女足/特选队/俱乐部同名,须national=1过滤或从resolve_match取team_id |
| G06/G13 | routing_gap | **球队名别名/音译消歧**:"清水鼓动"→"清水心跳"、"维尼亚德马埃弗顿"→"埃弗顿VM"、"吉普"→"基柏",resolve_team aliases覆盖不全 |
| F02/F04 | routing_gap | "艾阿利"→"麦纳麦国民",Al-Ahli高歧义跨联赛同名需competition_id过滤 |
| G12 | routing_gap | **历史场主客反转碰撞**:2018世界杯韩国vs墨西哥旧场若用户改述"韩国对墨西哥"将碰撞须date消歧 |

### 低优先级(数据/编排)
| type_id | gap 类型 | 描述 |
|---|---|---|
| F01 | completeness | get_odds_snapshot LIMIT 5截断(DB实有19欧/17亚),全量需SQL直查 |
| G03/G05 | data_gap | 继承上游data_gap(竞彩001/004当前期不存在);G05前序对象DB不存在 |
| G07 | context_gap | turn2跨窗口引用需checkpointer跨session共享 |
| F07 | 数据语义 | 阶段错位(比赛stage=淘汰赛,积分榜stage=小组赛);"赛果影响"在淘汰赛=晋级/出局 |

## 三、关键洞察

1. **F 场景赔率工具链成熟稳定**:Phase 2 重构后 get_odds_snapshot/get_odds_trend/get_kelly/get_over_under_odds/get_half_odds/get_official_handicap_odds 六大赔率工具全部返回结构化数据(initial/current/latest三态+多公司),F 场景 9/10 干净通过,仅 F03 篮球分支缺口。

2. **get_odds_trend 两个新发现的 implementation_gap**:①硬编码 football 表对篮球 DATA_MISSING(F03);②只覆盖欧赔时序不含亚盘 handicap 时序(F09/G16)。两者均有 SQL 分区表 workaround(football_odds_asian_change_YYYYMM / basketball_odds_europe_change_YYYY),P3 优先补全工具层。

3. **G 场景多轮追问方法论验证成功**:20 个 G 场景中,turn1 maintain_context/delegate_subagent/synthesize 编排类 atomic 全部归 agent_layer_covered,工具层只验证数据可得性。该方法论有效区分了工具层 vs 编排层职责,16/20 干净通过。

4. **resolve_lottery_match 竞彩编码路由是跨批次最高频问题**:G01/G09/G14/E05/E06 均报告裸 code ENTITY_NOT_FOUND,须带星期前缀+date;lottery entries match_id=null 须 resolve_match(队名+date)回填。这是 P3 必修项(影响所有竞彩编号场景)。

5. **resolve_team 国家队/别名消歧是第二高频问题**:E10/G04/G09/G18 国家队首候选常为 U 系列/女足,G06/G13 球队名别名/音译消歧。resolve_team aliases 表覆盖不全,P3 需扩充。

6. **G08 篮球深度模板无解是跨批次架构问题**:与 B02/B08/B09/C07/D07 同源,篮球深度工具(效率/Pace/三分%/盘口/injury)完全缺失,所有篮球深度分析场景均受阻。这是 Phase 3 最重要的架构补全方向。

7. **G11 用户纠正场景从历史 blocked 升级 pass**:验证了 agent 编排层纠正能力 + 工具层重新 resolve 正确实体的完整闭环,intel_tags 直接佐证用户纠正事实。

## 四、产出文件
- data/eval/path_attempts/F01-F10.yaml(10 个)
- data/eval/path_attempts/G01-G20.yaml(20 个,部分覆盖P0已有文件)
- data/eval/batch_FG_summary.md(本文件)
