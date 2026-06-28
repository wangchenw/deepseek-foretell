# Foretell 数据库 Schema 地图(供探索智能体导航)

> 本文档是给评估探索智能体的数据库导航图。**不是强制路径**,只是帮你知道库里有什么表、各自装什么数据、对应哪类用户需求。你可以自由探索,跨表 JOIN,直查 SQL。foretell 工具是参考但不强制使用。

## 一、需求维度 → 表 快速映射

| 用户需求维度 | 主要表 | 备注 |
|---|---|---|
| 足球赛程/比分/状态 | football_match | status_id 见下方枚举;match_time_str 是北京时间字符串 |
| 篮球赛程/比分/状态 | basketball_match | status_id 枚举与足球不同,见下方 |
| 球队实体(足球) | football_team | national=1 是国家队;name_zh/name_en/short_name_zh |
| 球队实体(篮球) | basketball_team | 与 football_team 共享同一 id 整数空间,**有跨运动碰撞风险** |
| 赛事(足球) | football_competition | type:1联赛/2杯赛/3友谊赛;id=1 是世界杯 |
| 赛事(篮球) | basketball_competition | |
| 赛季 | football_season / basketball_season | is_current=1 是当前赛季;**取积分榜/统计时务必过滤 season_id=当前赛季** |
| 积分榜(足球) | football_points_table + football_points_table_team | 父表 football_points_table 含 competition_id+season_id+stage_id;子表 football_points_table_team 含 position/points/won/draw/loss/goals/goals_against,主客分列 |
| 积分榜(篮球) | basketball_points_table + basketball_points_table_team | |
| 射手榜 | football_competition_shooters | season_id+position+team_id+player_id+goals+penalty+assists+minutes_played |
| 球员赛季统计 | football_competition_players_stats | 全维度统计(射门/传球/抢断/解围/控球率等),uid=seasonId_teamId_playerId |
| 球队赛季统计 | football_competition_teams_stats | 全维度统计,uid=seasonId_teamId;**foretell get_team_season_stats 是 stub,直接 SQL 查这张表** |
| 球队阵容(大名单) | football_team_squad | team_id+player_id+position+shirt_number+is_captain |
| 比赛首发/阵型 | football_match_lineup + football_match_lineup_detail | 父表 lineup 含 match_id+confirmed+home_formation+away_formation;子表 detail 含 22 球员 first/captain/shirt_number/position/x/y/rating;**foretell get_match_lineup 是 stub,直接 SQL 查** |
| 球队伤停 | football_team_injury | team_id+player_id+type(1受伤/2停赛/3出战成疑)+reason+missed_matches |
| 比赛关联伤停 | football_match_team_injury | match_id+team_injury_id 中间表 |
| 比赛情报(简洁) | football_intelligence | id=match_id;good_home/good_away/bad_home/bad_away/neutral(各 varchar 3000) |
| 比赛情报(详细) | football_match_intelligence | 更详细情报接口 |
| 实时文字直播 | football_match_tlive | match_id+main+type+position(0中立/1主/2客)+time+data;**live 场景核心表** |
| 比赛事件 | football_match_incidents | 红黄牌/换人等 |
| 比赛统计(球队) | football_match_team_stats / football_match_stats | |
| 比赛统计(球员) | football_match_player_stats | |
| 半全场统计 | football_match_half_team_stats / football_match_victory_defeat | |
| 进失球概率 | football_match_goals_lost_rate | |
| 欧赔 | football_odds_europe | match_id+company_id+first_odd1/2/3(初盘)+odd1/2/3(即时)+real_odd1/2/3(最新)+is_zoudi(走地) |
| 亚盘 | football_odds_asian | |
| 大小球 | football_odds_over_down | |
| 半场赔率 | football_odds_half_europe / half_asian / half_over_down | |
| 角球赔率 | football_odds_corner / half_corner | |
| 百欧赔 | football_odds_hundred_europe | |
| 官方让球胜平负 | football_odds_official_handicap | |
| 必发指数 | football_bf | |
| 同赔历史(亚盘) | football_asian_match_index | 初指相同赛事统计 |
| 同赔历史(欧赔) | football_europe_match_index | 指数异动赛果统计 |
| 系列赛对阵(足球) | football_bracket_match_up | round_id+home_team_id+away_team_id+winner_team_id+home_score/away_score(多回合=胜场次数)+match_ids(关联比赛id 列表)+type_id(1单场/8三局两胜/9五局三胜/10七局四胜) |
| 系列赛对阵(篮球) | basketball_bracket_match_up | 同上结构;**NBA 季后赛 G7 在这里,type_id=10 表示七局四胜** |
| 系列赛阶段 | football_bracket_rounds / basketball_bracket_rounds | |
| 系列赛对阵图 | football_brackets / basketball_brackets | |
| 升降级 | football_promotions / basketball_promotions | |
| 冠亚军 | football_first_second_info | |
| FIFA 排名 | football_fifa_ranking | 国家队 |
| 俱乐部排名 | football_club_ranking | |
| 竞彩足球赔率/彩果 | lottery_jczq_odds / lottery_jczq_result | spf/rq/bf/jq/bqc 全玩法;issue+issue_num(期号+序号) |
| 竞彩篮球赔率/彩果 | lottery_jclq_odds / lottery_jclq_result | |
| 北单赔率/彩果 | lottery_bd_odds / lottery_bd_result / lottery_bdsf_* | |
| 传统足彩十四场 | lottery_zc_issue + lottery_zc_match | issue(期号)+type(sfc/bqc/jqc/rj);lottery_zc_match 含 match_id+comp+home+away+result |
| 体彩比赛关联 | lottery_match | lottery_type+issue+issue_num+home_name+away_name+match_id(常为 null,需用 name+date 模糊匹配回 football_match) |
| 球员基础 | football_player / basketball_player | |
| 球员身价 | football_player_market | |
| 球员转会 | football_player_transfer / basketball_player_transfer | |
| 球员荣誉 | football_player_honor / basketball_player_honor | |
| 球队荣誉 | football_team_honor / basketball_team_honor | |
| 教练 | football_coach / basketball_coach + coach_history / coach_honor | |
| 裁判 | football_referee | |
| 场馆 | football_venue / basketball_venue | |
| 赛事最佳 | football_season_best_player / best_team / best_lineup | |
| 新闻/资讯 | cms_news / football_cms_news | |
| 心水推荐 | data_macao_recommend | |

## 二、关键状态码枚举

### football_match.status_id
0异常/1未开赛/2上半场/3中场/4下半场/5加时赛/7点球决战/8完场/9推迟/10中断/11腰斩/12取消/13待定

**常用过滤**:
- 进行中:`status_id IN (2,3,4,5,7)`
- 未开赛(未来):`status_id=1`(注意 match_time_str 升序)
- 已完赛:`status_id=8`
- **重要**:`status_id IN (1,2,3,4,5,9)` 配 `match_time >= NOW()` 才是真正的"未来或进行中"

### basketball_match.status_id
0异常/1未开赛/2第一节/3第一节完/4第二节/5第二节完/6第三节/7第三节完/8第四节/9加时赛/10完场/11中断/12取消/13延期/14腰斩/15待定

### basketball_match.kind
1常规赛/2季后赛/3季前赛/4全明星/5杯赛/6附加赛/0无

### bracket_match_up.type_id(系列赛赛制)
1单场决胜/8三局两胜/9五局三胜/10七局四胜(**G7 = type_id=10 且当前 home_score+away_score=6 即第7场**)

### bracket_match_up.state_id
1未开赛/2等待对手/6进行中/7主场胜/8客场胜/9取消/10轮空/11等待抽签

### football_team_injury.type
1受伤/2停赛/3出战成疑/0未知

### football_match_incidents.type（技术统计码，纳米状态码文档权威）
1进球/2角球/3黄牌/4红牌/5越位/6任意球/7球门球/8点球/9换人/10比赛开始/11中场/12结束/13半场比分/15两黄变红/16点球未进/17乌龙球/18助攻/19伤停补时/21射正/22射偏/23进攻/24危险进攻/25控球率/26加时赛结束/27点球大战结束/28 VAR/29点球(点球大战)/30点球未进(点球大战)/37射门被阻挡/38补水

### football_match_incidents.reason_type（事件原因码，纳米状态码文档权威）
0未知/1犯规/2个人犯规/3侵犯对手或受伤换人/4战术犯规或战术换人/5进攻犯规/6无球犯规/7持续犯规/8持续侵犯/9暴力行为/10危险动作/11手球犯规/12严重犯规/13故意犯规/14阻挡进球机会/15拖延时间/16视频回看裁定/17判罚取消/18争论/19对判罚表达异议/20犯规和攻击言语/21过度庆祝/22没回退到要求距离/23打架/24辅助判罚/25替补席/26赛后行为/27其他原因/28未被允许进入场地/29进入比赛场地/30离开比赛赛场/31非体育道德行为/32非主观意愿恶意犯规/33假摔/34干预var复审/35进入裁判评审区/36吐口水/37病毒

### football_player_transfer.transfer_type（纳米 openapi 字段说明权威）
1租借/2租借结束/3转会/4退役/5选秀/6已解约/7已签约/8未知

### football_player.preferred_foot（纳米 openapi 字段说明权威）
0未知/1左脚/2右脚/3左右脚

### basketball_player.position（DB 列注释权威）
C中锋/SF小前锋/PF大前锋/SG得分后卫/PG组织后卫/F前锋/G后卫

### basketball_player.preferred_hand（DB 列注释权威）
1左手/2右手/3左右手

### 指数公司ID（company_id，纳米状态码文档权威）
2 BET365/3皇冠/4 10BET/5立博/6明陞/7澳彩/8 SNAI/9威廉希尔/10易胜博/11韦德/12 EuroBet/13 Inter wetten/14 12bet/15利记/16盈禾/17 18Bet/18 Fun88/19竞彩官方/20 onex/21 188/22平博/136马会

> 以上映射已固化在 `foretell/tools/crazy_sports/mysql_client.py` 的 `_INCIDENT_TYPE_MAP`/`_INCIDENT_REASON_MAP`/`_TRANSFER_TYPE_MAP`/`_PREFERRED_FOOT_MAP`/`_BASKETBALL_POSITION_MAP`/`_PREFERRED_HAND_MAP`/`_STATUS_MAP` 等常量，工具返回时自动还原为语义字符串，LLM 无需自行解码裸数字。

## 三、关键表列结构(探索时少调 schema)

### football_match(比赛主表)
- id, season_id, competition_id, home_team_id, away_team_id
- status_id(见枚举), match_time(int 时间戳), match_time_str(varchar 北京时间)
- home_scores, away_scores(varchar "[常规,半场,红牌,黄牌,角球,加时,点球]")
- home_position, away_position(varchar 排名)
- coverage_lineup(1有阵容), coverage_intelligence(1有情报), coverage_mlive(1有动画)
- neutral(1中立场), venue_id, referee_id
- round_stage_id, round_group_num, round_num
- related_id(双回合另一回合 id), home_agg_score, away_agg_score(总比分)

### football_team(球队)
- id, name_zh, name_en, short_name_zh, show_name_zh
- national(1国家队/0俱乐部), country_id, competition_id(所属联赛)
- gender(1男/2女), virtual(1占位球队)
- uid(合并后对应 id), market_value, total_players, foreign_players, national_players

### football_competition(赛事)
- id, name_zh, name_en, short_name_zh
- type(0未知/1联赛/2杯赛/3友谊赛), category_id, country_id
- title_holder, most_titles, newcomers, divisions(赛事层级)
- level, show_flag, order_sort

### football_points_table(积分榜父表)
- id, competition_id, season_id, stage_id, conference, group

### football_points_table_team(积分榜子表——**查积分榜用这张**)
- uid(tableId_teamId), table_id, team_id, promotion_id
- points, position, deduct_points, total, won, draw, loss, goals, goals_against, goal_diff
- home_points/position/total/won/draw/loss/goals/goals_against/goal_diff
- away_points/position/total/won/draw/loss/goals/goals_against/goal_diff

**查积分榜标准 SQL**:
```sql
SELECT pt.team_id, t.name_zh, pt.position, pt.points, pt.won, pt.draw, pt.loss, pt.goals, pt.goals_against
FROM football_points_table p
JOIN football_points_table_team pt ON pt.table_id = p.id
JOIN football_team t ON t.id = pt.team_id
WHERE p.competition_id = ? AND p.season_id = (SELECT MAX(season_id) FROM football_points_table WHERE competition_id = ?)
ORDER BY pt.position LIMIT 30
```

### football_competition_teams_stats(球队赛季统计——**get_team_season_stats 是 stub,查这张**)
- uid(seasonId_teamId), season_id, team_id
- matches, goals, penalty, assists, red_cards, yellow_cards
- shots, shots_on_target, dribble, dribble_succ, clearances, blocked_shots, tackles
- passes, passes_accuracy, key_passes, crosses, crosses_accuracy, long_balls
- duels, duels_won, aerial_won, aerial_lost, ground_won, ground_lost
- fouls, was_fouled, goals_against, interceptions, offsides, corner_kicks
- ball_possession, freekicks, freekick_goals, hit_woodwork, fastbreaks, poss_losts

### football_competition_shooters(射手榜——**无原生工具,查这张**)
- uid(seasonId_position), season_id, position, team_id, player_id
- goals, penalty, assists, minutes_played

### football_competition_players_stats(球员赛季统计)
- uid(seasonId_teamId_playerId), season_id, team_id, player_id
- matches, court, first, goals, penalty, assists, minutes_played
- red_cards, yellow_cards, shots, shots_on_target, dribble, passes, key_passes...
- saves, punches, runs_out, clean_sheets(守门员字段)

### football_match_lineup(比赛阵容父表)
- id, match_id, confirmed(1正式), home_formation, away_formation, home_coach_id, away_coach_id, home_color, away_color

### football_match_lineup_detail(阵容详情——**get_match_lineup 是 stub,查这张**)
- id, lineup_id, team_id, player_id
- first(1首发/0替补), captain(1队长), name, shirt_number, position(F/M/D/G), x, y, rating, incidents

**查首发标准 SQL**:
```sql
SELECT ld.team_id, ld.first, ld.captain, ld.name, ld.shirt_number, ld.position, ld.rating
FROM football_match_lineup l
JOIN football_match_lineup_detail ld ON ld.lineup_id = l.id
WHERE l.match_id = ? AND l.confirmed = 1 AND ld.first = 1
ORDER BY ld.team_id, ld.shirt_number LIMIT 30
```

### football_team_squad(球队大名单)
- team_id, player_id, position(F/M/D/G), shirt_number, is_captain, has_shirt_number

### football_team_injury(球队伤停)
- team_id, player_id, competition_id, type(1受伤/2停赛/3出战成疑/0未知), reason, start_time, end_time, missed_matches, del_flag(1正常/-1删除)

### football_intelligence(比赛情报简洁版)
- id(=match_id), good_home, good_away, bad_home, bad_away, neutral(各 varchar 3000)

### football_match_tlive(实时文字直播——**live 场景核心**)
- match_id, main(1重要事件), type, position(0中立/1主/2客), time(分钟), data(内容), sort

### football_odds_europe(欧赔)
- match_id, company_id, match_time, status_id, score
- first_odd1/2/3(初盘主胜/和/客胜), odd1/2/3(即时), real_odd1/2/3(最新), pre_odd1/2/3
- is_zoudi(0否/1走地), is_entertained(0否/1封盘)

### basketball_match(篮球比赛)
- id, competition_id, home_team_id, away_team_id, season_id
- kind(1常规赛/2季后赛/3季前赛), status_id(见枚举), match_time, match_time_str
- home_scores, away_scores("[节1,节2,节3,节4,加时]"), over_time_scores
- home_position, away_position, coverage_intelligence, has_players
- round_stage_id, round_group_num, round_round_num
- timer_*(实时数据:更新时间/走秒/倒计时/小节剩余时间)

### basketball_team(篮球队)
- id, name_zh, name_en, short_name_zh, national, conference_id(1大西洋/2中部/3东南/4太平洋/5西北/6西南/7-10 NBA杯赛组)
- competition_id, coach_id, uid, virtual, gender

### basketball_bracket_match_up(篮球系列赛对阵——**NBA G7 在这里**)
- id, round_id, number, type_id(1单场/8三局两胜/9五局三胜/10七局四胜)
- state_id(1未开赛/6进行中/7主场胜/8客场胜)
- home_team_id, away_team_id, winner_team_id, home_score, away_score(多回合=胜场次数)
- parent_id(下一对阵), children_id1/2(上一对阵), match_ids(关联比赛 id 列表)

**查 G7 标准 SQL**:
```sql
SELECT bu.id, bu.home_team_id, bu.away_team_id, bu.home_score, bu.away_score, bu.state_id,
       ht.name_zh AS home, at.name_zh AS away
FROM basketball_bracket_match_up bu
JOIN basketball_team ht ON ht.id = bu.home_team_id
JOIN basketball_team at ON at.id = bu.away_team_id
WHERE bu.type_id = 10 AND (bu.home_score + bu.away_score) = 6
LIMIT 20
```

### lottery_zc_match(传统足彩十四场)
- id, type(sfc胜负彩/bqc半全场/jqc进球彩/rj任九), issue(期号)
- match_id, comp, home, away, match_time, match_time_str, result

### lottery_zc_issue(传统足彩期次)
- id, type, issue, start_time, end_time, draw_time, result
- first_pot_count, first_prize, second_pot_count, second_prize, jackpot, sales

### lottery_jczq_odds(竞彩足球赔率)
- id, comp, home, away, short_comp, short_home, short_away
- issue, issue_num(序号), match_time, match_time_str
- sell_status(0未开售/1仅过关/2单关和过关/3停售)
- spf(胜平负), rq(让球), bf(比分), jq(进球数), bqc(半全场), cancel

### football_season(赛季)
- id, competition_id, year, start_time, end_time, is_current(1当前赛季)
- has_player_stats, has_team_stats, has_table(是否有积分榜)

## 四、已知的 foretell 工具层问题(探索时参考,不阻塞你找 SQL 路径)

> **Phase 2 工具层重构已完成(类 1 抽象修复 5 项 + 类 2 补覆盖 38 新工具 + 8 stub 实现)。** 下表中标注 ✅ 的工具已修复/实现,可正常调用;标注 🆕 的是 Phase 2 新增工具。以下保留历史问题记录供溯源,但多数已不再是问题。

### ✅ 已修复(Phase 2 类 1 抽象修复)

| 工具 | 修复内容 |
|---|---|
| get_h2h / get_match_result | ✅ 比分数组解码为 `score_breakdown:{full,half,red_card,yellow_card,corner,overtime,penalty}`,移除 raw 数组 |
| get_odds_snapshot | ✅ 欧赔 `odd1/2/3`→`{home_win,draw,away_win}`;亚盘→`{handicap,home_line,away_line}`;加 `company_name`;`is_zoudi/is_entertained`→`in_play/suspended` 布尔 |
| get_standings | ✅ 加 `MAX(season_id)` 过滤当前赛季;补 `goals/goals_against/goal_diff` + 主客分列;结构化返回 |
| resolve_match | ✅ 修 series_game 反转 bug(原 `if series_game is not None: return []`,现正常查) |
| resolve_lottery_match / get_lottery_schedule | ✅ 竞彩赔率结构化:`spf/rq/bf/jq/bqc/sf/rf/dxf/sfc` 拆解;`sell_status` 映射中文;`play_type` 加 `play_type_desc` |

### ✅ 已实现(Phase 2 类 2 批 2,原 stub)

| 工具 | 实现表 |
|---|---|
| get_team_season_stats | ✅ football_competition_teams_stats |
| get_match_lineup | ✅ football_match_lineup + _detail |
| get_injury_report | ✅ football_team_injury(type 1受伤/2停赛/3出战成疑已映射) |
| get_intel_tags | ✅ football_intelligence |
| get_betfair | ✅ football_bf |
| get_odds_trend | ✅ football_odds_europe_change_*(历史分区) |
| get_same_odds_history | ✅ football_asian_match_index / football_europe_match_index |
| get_kelly | ✅ 由 football_odds_europe 反推 |

### 🆕 Phase 2 新增工具(类 2 批 1+3+4,共 33 个)

| 工具 | 数据表 | 维度 |
|---|---|---|
| get_top_scorers | football_competition_shooters | 射手榜 |
| get_team_squad | football_team_squad | 大名单 |
| get_series_matchup | football/basketball_bracket_match_up | 系列赛对阵图(G7) |
| get_basketball_standings | basketball_points_table_team | 篮球积分榜 |
| get_match_tlive | football_match_tlive | 实时文字直播 |
| get_match_incidents | football_match_incidents | 红黄牌/换人事件 |
| get_match_team_stats | football_match_team_stats | 球队比赛统计 |
| get_match_player_stats | football_match_player_stats | 球员比赛统计 |
| resolve_basketball_team | basketball_team | 🆕 篮球球队解析(避免跨运动 ID 碰撞) |
| resolve_basketball_league | basketball_competition | 🆕 篮球赛事解析 |
| get_seasons | football/basketball_season | 赛季列表(is_current 过滤) |
| get_player_profile | football/basketball_player | 球员资料 |
| get_player_market_value | football_player_market | 球员身价历史 |
| get_player_transfers | football/basketball_player_transfer | 球员转会 |
| get_player_honors | football/basketball_player_honor | 球员荣誉 |
| get_team_honors | football/basketball_team_honor | 球队荣誉 |
| get_coach | football/basketball_coach | 教练资料 |
| get_referee | football_referee | 裁判资料 |
| get_venue | football/basketball_venue | 场馆资料 |
| get_match_half_stats | football_match_half_team_stats | 半全场统计(scope: ft/p1/p2/o1/o2) |
| get_goals_lost_rate | football_match_goals_lost_rate | 进失球概率 |
| get_over_under_odds | football_odds_over_down | 🆕 大小球赔率(语义 over/total/under) |
| get_half_odds | football_odds_half_europe/half_asian/half_over_down | 🆕 半场赔率(欧/亚/大小球) |
| get_corner_odds | football_odds_corner/half_corner | 🆕 角球赔率(全场/半场) |
| get_hundred_europe_odds | football_odds_hundred_europe | 🆕 百欧赔率 |
| get_official_handicap_odds | football_odds_official_handicap | 🆕 官方让球盘 |
| get_promotions | football/basketball_promotions | 🆕 升降级 |
| get_first_second | football_first_second_info | 🆕 冠亚军 |
| get_fifa_ranking | football_fifa_ranking | 🆕 FIFA 排名 |
| get_club_ranking | football_club_ranking | 🆕 俱乐部排名 |
| get_season_best | football_season_best_player/best_team | 🆕 赛季最佳 |
| get_recommendations | data_macao_recommend | 🆕 心水推荐 |

### 仍需注意的历史问题(部分场景可能仍触发)

| 工具 | 问题 | 规避 |
|---|---|---|
| get_team_schedule direction=upcoming | schedule.py 语义反转返回历史升序 | SQL: `WHERE status_id IN(1,2,3,4,5,9) AND match_time>=NOW() ORDER BY match_time` |
| get_team_schedule league_id | schedule.py 过滤器失效 | SQL WHERE competition_id=? |
| honor_id 未映射名称 | 球员/球队荣誉表 honor_id 是数字 ID,荣誉字典表未 JOIN | 返回 honor_id + season + competition_id,LLM 可据上下文推断 |

## 五、探索工具入口

```bash
# 列工具签名
uv run python scripts/foretell_eval_helper.py list-tools

# 调 foretell 工具
uv run python scripts/foretell_eval_helper.py tool <name> '<json_args>'

# 只读 SQL(强制 SELECT + 自动 LIMIT)
uv run python scripts/foretell_eval_helper.py sql "<SELECT ... LIMIT N>"

# 查表结构(模糊匹配)
uv run python scripts/foretell_eval_helper.py schema <keyword>
```

**安全约束**:sql 子命令仅允许 SELECT;出现 INSERT/UPDATE/DELETE/ALTER/DROP/CREATE 等关键字直接拒绝;未写 LIMIT 自动追加 LIMIT 200。

## 六、探索原则(重要)

1. **目标是找到能回答用户问题的数据路径,不是诊断工具 bug**。foretell 工具坏不等于无解——只要数据库有数据能回答用户,就是"有路径"。
2. **数据库有数据 = 有路径(⚠️ 或 ✅);数据库也查不到 = 真无解(❌)**。
3. 遇到 foretell 工具返回空/异常时,**先 SQL 直查对应表确认数据是否真的不存在**,再下结论。
4. 跨表 JOIN 是允许且鼓励的——很多需求需要 JOIN 多张表(如积分榜要 JOIN football_points_table + football_points_table_team + football_team)。
5. season_id 过滤是常见坑——查积分榜/统计/射手榜时务必确认取的是当前赛季(MAX(season_id) 或 football_season.is_current=1)。
6. 篮球类问题用 basketball_* 表,不要把篮球 team_id 传给足球工具。
