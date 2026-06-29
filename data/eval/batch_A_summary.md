# Foretell LLM Eval v2 — A 场景重试批次汇总(18 类型)

执行时间:2026-06-28 ~ 2026-06-29
方法论:**LLM 自主判断**(抛弃死板评分规则)。探索智能体只给目标+DB schema 地图,自主探索查询链路;审查智能体用 LLM 判断力分析查询链路,产出 ✅/⚠️/❌ 三分类+定性判断,不打分。
本批次覆盖:A01-A18(A08/A17 复用 P0 产出,其余 16 个为本轮重跑)。

## 一、总表(✅/⚠️/❌ 三分类)

| type_id | 名称 | 分类 | 关键 gap(P1) | SQL workaround |
|---|---|---|---|---|
| A01 | 按日期热门赛程 | ✅ | routing_gap P1(口语001≠周六067) | 有(football_odds_europe 替代 get_odds_trend) |
| A02 | 指定联赛日期赛程 | ⚠️ | routing_gap P1(里斯本竞技别名缺失) | 有(SQL 直查 football_match 拿 match_id) |
| A03 | 球队未来赛程 | ⚠️ | tool_logic_gap P1(get_recent_form 无 before_date) | 有(SQL match_time<比赛时间) |
| A04 | 球队近期赛程 | ⚠️ | data_gap P1(无 xG 字段)+ tool_logic_gap P1(get_recent_form) | 有(6/7 维度,仅 XG 真缺) |
| A05 | 实时比分查询 | ⚠️ | 5 个 stub P1(lineup/injury/intel/stats/trend) | 有(全部 SQL 替代表验证) |
| A06 | 完场赛果 | ⚠️ | 3 个 stub P1(trend/betfair/kelly) | 部分(初盘可 SQL,走势历史分区未深验) |
| A07 | 时间窗_今晚 | ✅ | —(4 个彩票码原生可解) | 有(北单 SQL 补 match 对齐) |
| A08 | 时间窗_明早 | ✅(P0) | tool_logic_gap P1(upcoming 语义反转) | 有(lottery 兜底,P0 已验证) |
| A09 | 时间窗_几点开赛 | ⚠️ | implementation_gap P1(无在玩列表/实时比分工具) | 有(football_match WHERE status_id IN(2,3,4)+tlive) |
| A10 | 积分榜 | ⚠️ | tool_logic_gap P1(get_standings 缺 season_id) | 有(SQL football_points_table_team WHERE season_id=MAX) |
| A11 | 射手榜 | ✅ | implementation_gap P1(无原生射手榜工具) | 有(SQL football_competition_shooters) |
| A12 | 球队赛季统计 | ✅ | implementation_gap P1(get_team_season_stats stub) | 有(SQL football_competition_teams_stats) |
| A13 | 历史交锋 | ⚠️ | routing_gap P1(浦项制铁别名缺一线队) | 有(SQL 双向查 football_match) |
| A14 | 球队阵容 | ⚠️ | implementation_gap P1(get_match_lineup stub) | 有(SQL lineup+detail+squad) |
| A15 | 比赛首发 | ✅ | 5 个 stub P1(lineup/kelly/injury/intel/betfair) | 有(SQL football_match_lineup_detail,关键纠正 issue=260516) |
| A16 | NBA赛程 | ✅ | tool_logic_gap P1(跨运动 ID 碰撞) | 有(basketball_match+NBA 路径) |
| A17 | 实体消歧_国家队 | ✅(P0) | — | —(P0 已验证) |
| A18 | 语义精度_锁定排名 | ✅ | tool_logic_gap P1(get_standings 缺 season_id) | 有(SQL 积分榜+剩余轮次计算验证锁定成立) |

**分类统计**:
- ✅ 找到可行路径(数据正确,路径清晰):**9 个**(A01, A07, A08, A11, A12, A15, A16, A17, A18)
- ⚠️ 找到路径但有隐患(路径存在但需修 bug 或 workaround 脆弱):**9 个**(A02, A03, A04, A05, A06, A09, A10, A13, A14)
- ❌ 穷尽探索后确认无解:**0 个**

## 二、与首跑对比(方法论成效验证)

| 指标 | 首跑(死板评分规则) | 重试(LLM 自主判断) |
|---|---|---|
| ✅ 干净通过 | 4 个(A01,A08,A11,A17) | **9 个**(+5:A07,A12,A15,A16,A18) |
| ⚠️ 有隐患 | 4 个(A03,A06,A13,A16) | **9 个**(+5:A02,A04,A05,A09,A10,A14 转入) |
| ❌ 穷尽无解 | **10 个** | **0 个** |
| pass 率 | 22%(4/18) | 50%(9/18,按 ✅ 计) |
| 找到 SQL workaround | 部分 | **全部 16 个重跑 case** |

**关键转变**:首跑 10 个 ❌ 全部改判——9 个升 ⚠️、1 个(A15)升 ✅。根因是首跑把"foretell 工具 stub/坏"等同于"无解",重试智能体在 DB schema 地图导航下主动探索 SQL 直查路径,发现几乎所有"工具坏"的 case 数据库都有数据,只是 foretell 工具层没实现。LLM 自主判断比死板评分规则更能识别"工具坏但数据在"的真实情况。

## 三、本轮新发现/确认的 gap(按类型)

### tool_logic_gap(工具返回错误数据或语义错误,P1)
| gap | 涉及 case | SQL workaround |
|---|---|---|
| get_standings 缺 season_id 过滤,多赛季合并 position=1 | A10, A18 | football_points_table_team WHERE season_id=MAX |
| get_team_schedule direction=upcoming 语义反转 | A03(首跑 A05-A09 复现) | football_match WHERE status_id IN(1,2,3,4,5,9) AND match_time>=NOW() |
| get_recent_form 无 before_date,赛前分析误用赛后数据 | A03, A04 | SQL match_time<比赛时间 AND status_id=8 |
| 跨运动 ID 碰撞(篮球 team_id 传足球工具静默返回足球数据) | A16 | basketball_* 表 |

### implementation_gap(工具 stub,SQL 替代表已验证)
| 工具 | 代码位置 | SQL 替代表 | 涉及 case |
|---|---|---|---|
| get_team_season_stats | mysql_client.py:724-725 | football_competition_teams_stats | A05,A10,A12 |
| get_match_lineup | 866-867 | football_match_lineup+detail | A05,A14,A15 |
| get_injury_report | 869-870 | football_team_injury | A05,A10 |
| get_intel_tags | 872-873 | football_intelligence | A05,A10 |
| get_odds_trend | 854-855 | football_odds_europe + _change_* | A01,A05,A06,A10 |
| get_kelly | 860-861 | 无独立表,由 football_odds_europe 反推 | A05,A06,A10,A15 |
| get_betfair | 863-864 | football_bf | A05,A06,A10,A15 |
| get_same_odds_history | 857-858 | football_asian/europe_match_index | A10,A18 |
| 无原生射手榜工具 | — | football_competition_shooters | A11 |
| 无在玩列表/实时比分工具 | — | football_match WHERE status_id IN(2,3,4)+tlive | A09 |

### routing_gap(参数/路由问题,P1-P2)
| gap | 涉及 case |
|---|---|
| resolve_match 别名不全(里斯本竞技=葡萄牙体育,浦项制铁=浦项铁人) | A02, A13 |
| resolve_team 词序容错(东京FC↔FC东京) | A05 |
| 竞彩编号口语 vs 工具格式(001≠周六067) | A01, A02 |
| lottery period 格式(YYYYMMDD→DATA_MISSING,须 YYMMDD) | A07 |
| lottery match_id=null 需 resolve_match 补 | A02, A06, A15, A18 |

### data_gap(数据库真无数据,需诚实说明)
| gap | 涉及 case | 性质 |
|---|---|---|
| XG/xGA 字段未采集 | A04, A05 | 真 data_gap,用 shots/shots_on_target 近似 |
| 冷门联赛球队覆盖不全(佐加顿斯/布鲁马波) | A04 | 真 data_gap |
| 冷门国家队 h2h 样本极少 | A01 | 真 data_gap |
| 个别场次不存在(纽卡vs桑德兰 2026-03-22) | A03 | 真 data_gap |
| 官方发布会/俱乐部官方信息无搜索入口 | A05, A07 | discover_via_search 评估约束 |

### context_gap(系统性,P2)
| gap | 涉及 case |
|---|---|
| 无原生 checkpointer,多轮上下文继承依赖 LLM 层显式串接 | A05,A08,A10,A12,A14,A16,A18 等多 case |

## 四、关键结论

1. **A 场景无真无解 case**(0 个 ❌)。所有 18 个 type_id 的用户问题都能在数据库找到数据支撑,只是部分维度(如 XG、官方发布会)需诚实说明数据缺失。

2. **9 个 ✅(50%)可直接给靠谱回答**:其中 A01/A07/A11/A12/A15/A16/A18 是本轮重跑新升 ✅,路径清晰数据正确;A08/A17 是 P0 已验证。

3. **9 个 ⚠️(50%)有路径但需修工具或依赖 LLM 层补丁**:主要集中在 foretell 工具层 8 个 stub(get_team_season_stats/get_match_lineup/get_injury_report/get_intel_tags/get_odds_trend/get_kelly/get_betfair/get_same_odds_history)和 2 个 tool_logic_gap(get_standings season_id 缺失、get_recent_form 无 before_date)。**这些都有 SQL 替代路径,Phase 2 修复工具或 Skill 层加 SQL fallback 即可全部升 ✅**。

4. **DB schema map 是关键赋能**:重试智能体拿到全表清单+需求维度映射+已知 stub 的 SQL 替代表后,能主动跨表 JOIN 找 workaround,不再卡在"工具坏=无解"。首跑缺这个地图,智能体只能逐个 schema 摸索,容易过早放弃。

5. **LLM 自主判断方法论验证成功**:抛弃 7 维度 rubric/cap 规则/pass>=3.5 阈值后,审查智能体能更准确识别"工具坏但数据在"的真实情况,不再被死板规则绑架把 ⚠️ 误判为 ❌。

6. **真 data_gap 集中在少数维度**:XG/xGA、冷门联赛覆盖、官方发布会、个别场次——这些是数据库本身的采集边界,不是工具层问题,LLM 层须按 expected_behaviors"数据不足时诚实说明"处理,不编造。

## 五、产出文件清单

- data/eval/db_schema_map.md(新增,DB 导航图)
- atomic_decompositions_v2/:A01-A18(16 个本轮+2 个 P0,atomic 复用不重写)
- path_attempts_v2/:A01-A18(16 个本轮重跑覆盖+2 个 P0,新格式 exploration_log)
- answer_playbooks_v2/:A01-A18(16 个本轮重跑覆盖+2 个 P0,新格式 classification+定性判断)

## 六、对后续批次的启示

1. **沿用 LLM 自主判断方法论**:B/C/D/E/F/G/H/X 批次都用这个方法,不再加评分规则。
2. **DB schema map 已就绪**:所有批次共享 db_schema_map.md,子智能体第一步 Read 即可获得导航。
3. **已知 stub 工具有 SQL 替代**:不必每个 case 重新验证 stub,直接用 SQL 替代表。
4. **真 data_gap 维度已知**:XG/官方发布会/冷门联赛覆盖,后续 case 涉及这些维度直接标 data_gap+诚实说明。
5. **context_gap 系统性**:多轮 case(G 类 20 个)都会遇到,Phase 2 统一规划 checkpointer。

## 七、Phase 2 工具层重构后 A 回归实跑验证(5 case 三智能体重跑)

Phase 2 全部完成(类 1 修复 5 项 + 类 2 批 1-4 共 38 新工具 + 8 stub 实现 + 状态码校正)。对 9 个 ⚠️ 中 4 个预期升档 case + A09 对照,派发 path-explorer-agent 实跑回归,并即时修复发现的 4 个新 bug。结果:

| type_id | 原 ⚠️ 原因 | Phase 2 修复 + 回归实跑 | 实际分类 |
|---|---|---|---|
| A05 | 5 个 stub(lineup/injury/intel/stats/trend) | 4 stub 实现 OK;**修复 2 个新 bug**:(1) get_odds_trend 月分区路由(隔月建表,odd_month 公式);(2) get_match_player_stats SQL 引用不存在的 s.position 列 → 改 first/minutes_played | ✅(升档) |
| A06 | 3 个 stub(trend/betfair/kelly) | betfair/kelly OK;**修复 extra.py 22 工具 make_envelope(source=) 签名 bug**;score_breakdown 语义化验证通过;trend 历史分区表 0 行属 data_gap(非阻塞) | ✅(升档) |
| A10 | get_standings 缺 season_id | season_id=MAX 过滤生效(position=1 唯一);goals/goal_diff/主客分列补齐 | ✅(升档) |
| A14 | get_match_lineup stub | lineup 实现 OK(阵型+首发+替补);**顺手修 minor gap**:detail 查询补 player_id 列 | ✅(升档) |
| A09(对照) | 无在玩列表/实时比分工具 | get_schedule_by_date 可按时间窗筛 + status 字段可本地过滤在玩;get_match_tlive 实时直播 OK;但无专用在玩列表工具 + limit=100 截断 | ⚠️(部分缓解,符合预期) |

**实际升档结果**:✅ 从 9 升到 **13**(+A05/A06/A10/A14),⚠️ 从 9 降到 **5**(A02/A03/A04/A09/A13),❌ 仍 0。

### 回归中即时修复的 4 个 bug(已全部修完 + tests 零回归)

1. **extra.py/player.py/tournament.py make_envelope(source=) 签名 bug**:22 个新工具全部崩溃(make_envelope 无 source 参数);修复:去掉非法 source=/sport=/gender= 等参数,业务字段移入 data dict
2. **get_match_player_stats SQL 引用 s.position**:football_match_player_stats 无 position 列,调用抛 1054;修复:改 SELECT s.first/s.minutes_played,_format_player_stats_row 输出 is_starter/minutes_played
3. **get_odds_trend 未路由月分区表**:仅查基表 0 行;修复:按 match_time 用 odd_month=(month-1)//2*2+1 公式路由到 football_odds_europe_change_YYYYMM(隔月建表),fallback 基表
4. **get_match_lineup detail 缺 player_id**:SELECT 漏 ld.player_id 列;修复:补 SELECT + _format_lineup_player 输出 player_id

### 仍 ⚠️ 的 5 个的修复路径(P3 候选)
- A02/A13(别名 routing_gap):扩展 resolve_team/resolve_match 别名库,或 Skill 层加别名映射
- A03/A04(get_recent_form 无 before_date):get_recent_form 加 before_date 参数
- A09(在玩列表):新增 get_live_matches 工具(football_match WHERE status_id IN(2,3,4,5))或 get_schedule_by_date 加 status_in 参数 + 扩容 limit

### 侧发现(P3 候选,不阻塞)
- get_basketball_standings 多 stage 混入(regular/playoff/summer league 同 season_id),需加 stage/group 过滤

