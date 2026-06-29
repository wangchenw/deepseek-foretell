# Foretell LLM Eval v2 — D+E 场景批次汇总(24 类型)

执行时间:2026-06-29
方法论:**LLM 自主判断**(沿用 A/X/B+C 方法论)。path-explorer-agent 实调 foretell tools 探索路径。
本批次覆盖:D01-D10(购彩推荐10) + E01-E14(批量串关14),分 5 波并发派发。

## 一、总表

### D 购彩推荐(10个)

| type_id | 名称 | 分类 | 关键发现 |
|---|---|---|---|
| D01 | 这场怎么买 | ⚠️ | 路径打通(get_lottery_schedule+bf31/jq8/bqc9),但用户说"四场"实际竞彩明日仅3场世界杯正赛,需澄清 |
| D02 | 主不败推荐 | ✅ | get_lottery_schedule(101)=15场含spf/rq/bf/jq/bqc;resolve_lottery_match 需完整code"周一074"去date;get_odds_snapshot+get_kelly OK |
| D03 | 让球推荐 | ✅ | SQL 直查 lottery_jczq_odds.rq 完整可得(rq=+1,1.70,3.85,3.55)+亚盘+情报+交锋;resolve_lottery_match 路由摩擦非阻塞 |
| D04 | 大小球推荐 | ✅ | get_over_under_odds+get_goals_lost_rate+get_schedule_by_date 三源;get_recommendations DATA_MISSING 非阻断 |
| D05 | 比分玩法 | ⚠️ | 北单 bf JSON 解析 bug:_parse_lottery_play 按 CSV 拆分导致25项丢失截断;SQL 层完整 |
| D06 | 单场方案 | ⚠️ | "1/2球"精确对应 lottery_jczq_odds.jq(8项);心水推荐 DATA_MISSING;5注已完赛为回顾性 |
| D07 | 篮球让分购彩 | ✅ | lottery_jclq_odds.rf 让分赔率已结构化;**跨运动碰撞 high 风险**(team_id 10505 篮球卡塔尔/足球索菲亚火车头),规避:禁用无sport参数的football deep工具 |
| D08 | 胜平负推荐 | ✅ | get_lottery_schedule(301 北单)=4场含bf25/spf/jq/bqc;spf.win 截断JSON小瑕疵不阻塞 |
| D09 | 稳胆推荐 | ⚠️ | **context_gap**:文案是方法论咨询未点名比赛,resolve_entity 无实体可消歧;底层稳胆数据路径完整 |
| D10 | 购彩风险提示 | ⚠️ | 明日仅3场无法组4串11;disclaimer 由 foretell-output-discipline skill 层强制保证(prompt_layer_covered) |

### E 批量串关(14个)

| type_id | 名称 | 分类 | 关键发现 |
|---|---|---|---|
| E01 | 扫盘 | ✅ | get_lottery_schedule(101)=15条单轮打通,赔率玩法维度齐全;6条未开盘场次 odds.spf=None 时序问题 |
| E02 | 四串一 | ✅ | 批次+实体回填链路打通,七大维度单场分析工具全可用非stub(recent_form/injury/intel/odds_snapshot/lineup/odds_trend/same_odds_history/betfair) |
| E03 | 三串一 | ✅ | get_lottery_schedule(101)=7场;resolve_match 简称别名缺失(布鲁马波→布洛马波卡纳),SQL LIKE fallback 打通 |
| E04 | 二串一 | ✅ | 同 E03 简称 routing_gap;2场客胜热门实际2:2平局印证"演戏"维度价值 |
| E05 | 十四场 | ⚠️ | **合成ID假命中bug仍存在实锤**:lottery返回合成match_id(260891)实指2009法国低级联赛而非2026世界杯真实id 4459720;resolve_match重解析规避 |
| E06 | 任九 | ⚠️ | **301≠任九**(301=北单胜负);任九rj属lottery_zc_match.type='rj'与401 sfc同表共享14场;foretell无rj专属play_type,易把sfc错认rj |
| E07 | 北单 | ⚠️ | 北单路由已通,比分可经lottery_bd_result确认;但"为什么赢"战术因果DB无数据(预备队/学院队未进football_match主库) |
| E08 | 今日竞彩列表 | ✅ | get_lottery_schedule 按 date 直查,101足球1场+201篮球4场;play_type隔离无跨运动碰撞 |
| E09 | 批量世界杯 | ✅ | 世界杯104场实体充足;get_schedule_by_date(tier=top)是批量入口;odds_trend/odds_snapshot/betfair三件套全OK |
| E10 | 初筛vs深核 | ✅ | 14个深度工具全OK;**resolve_team 国家队vs青训碰撞**(美国→女足U18,澳大利亚→特选队),正确team_id须从resolve_match获取 |
| E11 | 比分串方案 | ✅ | 24条竞彩批次含31项bf赔率;4场全resolve成功;get_match_result/goals_lost_rate/recent_form/h2h非stub |
| E12 | 在售方案 | ❌ | data_macao_recommend 8583条关联世界杯为0;世界杯预赛阶段Nami不产出心水,数据维度缺失 |
| E13 | 推荐N场 | ✅ | 批次入口可用;"最靠谱"是合成类任务非工具gap;half_odds+odds_snapshot+goals_lost_rate可排序 |
| E14 | 竞篮今日 | ✅ | get_lottery_schedule(201)正确路由lottery_jclq_odds,sf/rf/dxf/sfc全篮球玩法;play_type隔离无碰撞 |

**分类统计**:
- ✅ 找到可行路径:**15 个**(D02,D03,D04,D07,D08,E01,E02,E03,E04,E08,E09,E10,E11,E13,E14)
- ⚠️ 找到路径但有隐患:**8 个**(D01,D05,D06,D09,D10,E05,E06,E07)
- ❌ 穷尽探索后确认无解:**1 个**(E12)

## 二、新发现的 bug / gap(D+E 批次)

### 高优先级(工具层 bug,待全部跑完统一修)
| type_id | gap 类型 | 描述 | 修复路径 |
|---|---|---|---|
| D05/D08/E06/E07 | implementation_gap | **北单 odds JSON 解析 bug**:`_parse_lottery_play("bf"/"spf", raw)` 对北单 `lottery_bd_odds` 的 JSON 键值串统一按 CSV 拆分,导致赔率项丢失/截断(影响北单bf/spf玩法结构化) | `_parse_lottery_play` 增加 play_type=301/404 的 JSON 分支解析 |
| E05/E06 | routing_gap | **合成ID假命中bug仍存在**:lottery返回合成match_id(issue+issue_num拼接)与历史football_match.id数值碰撞;**任九无专属play_type**,401硬编码sfc与rj共享14场易错配 | 修复 resolve_lottery_match 返回真实match_id;新增 PlayType.RJ(如405)映射 lottery_zc_match.type='rj' |
| D07 | cross_sport_data_collision | 篮球team_id/match_id传入无sport参数的football deep工具静默返回足球数据(team_id 10505 篮球卡塔尔/足球索菲亚火车头) | 同 B08/C07,新增篮球版本工具或加sport参数;短期守轨:play_type隔离已规避lottery层,deep层仍需sport校验 |

### 中优先级(数据/语义)
| type_id | gap 类型 | 描述 |
|---|---|---|
| E12 ❌ | data_gap | data_macao_recommend 关联世界杯为0,世界杯预赛阶段Nami不产出心水推荐,数据维度缺失 |
| E07 ⚠️ | data_gap | 北单收录的预备队/学院队未进football_match主库,战术因果(lineup/stats/incidents)无match_id可挂;lottery_bd_result未由工具暴露 |
| D01/D10 ⚠️ | data_gap | 明日世界杯实际仅3场,用户"四场"/"4串11"前提与DB现实不符,需LLM澄清 |
| E10 | routing_gap | resolve_team 国家队成年组 vs 青训/特选队/女足碰撞(美国→女足U18),正确team_id须从resolve_match获取 |

### 低优先级(标注/澄清)
| type_id | gap 类型 | 描述 |
|---|---|---|
| D09 ⚠️ | context_gap | 文案是方法论咨询未点名比赛,atomic标注resolve_entity无实体可消歧,文案-分解错位 |
| E03/E04 | routing_gap | resolve_match 竞彩简称别名缺失(布鲁马波→布洛马波卡纳),SQL LIKE fallback 可打通 |

## 三、关键洞察

1. **竞彩 lottery 通道是 D/E 场景的核心数据源**:`get_lottery_schedule(play_type)` 路由到 `lottery_jczq_odds`(足球101)/`lottery_jclq_odds`(篮球201)/`lottery_bd_odds`(北单301)/`lottery_zc_match`(胜负彩401),含 spf/rq/bf/jq/bqc 全玩法赔率,直接覆盖购彩推荐与串关组合需求。Phase 2 重构后该通道稳定可用。

2. **北单 odds JSON 解析 bug 是新发现的高频问题**:D05/D08/E06/E07 四个涉及北单的 case 均报告 bf/spf 字段为截断 JSON 串,根因是 `_parse_lottery_play` 未对北单 JSON 键值串走 JSON 分支。这是 P3 优先修复项。

3. **合成 ID 假命中 bug 未修复且扩展到任九**:E05 实锤 lottery 返回合成 match_id 与历史 football_match.id 碰撞;E06 进一步发现任九 rj 与十四场 sfc 共享 14 场但 foretell 无 rj 专属 play_type,易把 sfc 错认成 rj。需新增 PlayType.RJ + 修复 match_id 返回。

4. **跨运动碰撞在 lottery 层已被 play_type 隔离规避**:D07/E14 篮球 case 通过 play_type(201) 路由到 `lottery_jclq_odds`,不静默返回足球数据;但 **deep 工具层仍无 sport 校验**(D07 实锤 team_id 10505 碰撞),篮球场景若误用 football deep 工具仍会 false positive。

5. **resolve_team 实体碰撞扩展到同运动内**:E10 发现 resolve_team("美国")首候选=女足U18、resolve_team("澳大利亚")首候选=特选队,都不是世界杯成年国家队。国家队场景正确 team_id 须从 resolve_match 获取,不能依赖 resolve_team 首候选。

6. **disclaimer 由 skill 层强制保证**:D10 验证 `foretell-output-discipline` SKILL.md 强制购彩建议回复含风险声明,工具层无 disclaimer 专用工具也无缺口,属 prompt_layer_covered。

7. **心水推荐表数据稀疏**:D04/D06/D09/E12/E13 均报告 `get_recommendations` 对目标场 DATA_MISSING,但表有 8583 行且抽样 OK,证明工具非 stub,仅世界杯/近期场次无心水数据覆盖(数据时序问题)。

## 四、产出文件
- data/eval/path_attempts/D01-D10.yaml(10 个)
- data/eval/path_attempts/E01-E14.yaml(14 个)
- data/eval/batch_DE_summary.md(本文件)
