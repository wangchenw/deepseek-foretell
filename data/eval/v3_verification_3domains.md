# foretell 工具层阶段 3 第一批重写验证报告

- 验证日期: 2026-06-30
- 验证范围: lottery / entity / standings + get_odds_trend 共 4 类修复,9 个撞墙场景
- 验证方式: 直连 MySQL 实跑 foretell.tools.crazy_sports.client(MySQLCrazySportsClient),对照 v2 path_attempts_v2 撞墙结论
- 验证脚本: 一次性运行后已清理(非代码改动),所有结论基于真实 DB 返回

## 一、验证结果总表

| 场景 | v2 结论 | 验证方法 | 实际结果 | 是否升档 |
|------|---------|----------|----------|----------|
| E05 | ⚠️ tool_logic_gap(合成 ID 假命中) | get_lottery_schedule(401, period=26089) 看 football_match_id | `lottery_official_id=260891`(合成)与 `football_match_id=4459720`(真实 巴西vs日本)分离,match_id 字段指向真实 ID。与 v2 SQL 基准完全一致 | ✅ |
| E07 | ⚠️ tool_logic_gap(北单 bf JSON 被按 CSV 切) | get_lottery_schedule(301) 看 bf 字段 | bf 返回结构化列表 `[{label:"3:1",odds:33.4},...,{label:"2:0",odds:31.33},...]`,JSON 解析修复。**但 spf 语义映射错位**(win/loss 互换、draw 丢失,见新问题 1) | ⚠️ |
| D05 | ⚠️ implementation_gap(北单 bf JSON 解析损坏) | get_lottery_schedule(301/404) 看 bf 字段 | 301 的 bf JSON 解析已修复(同 E07)。404 路径只返 sf(让球)不返 bf——D05 的比分玩法应走 301 而非 404,路由层须澄清。spf 语义同 E07 错位 | ⚠️ |
| B04 | ⚠️ implementation_gap(无 date 时 LIMIT 10 被青年/女足占满) | resolve_match(中国,日本,national=True) | 首候选 match_id=4146376 中国(11087)vs 日本(14529)世亚预 2024-11-19 男子 A 级,与 v2 SQL 基准一致。U17/U20/U23/女足已排除。残留:沙滩足球仍混入候选(见新问题 3) | ✅ |
| E10 | ⚠️ resolve_team("日本")返回 U 系列未命中成年队 | resolve_team(日本,national=True) | 首候选 team_id=14529 日本成年国家队(v2 中不在 top-10,现置顶)。U16/U17/U18/U21/女足已排除。残留:日本沙滩/室内/U24 仍混入(见新问题 3) | ✅ |
| A10 | ⚠️ tool_logic_gap(缺 season_id 过滤,多赛季合并 position=1) | get_standings(108) 意甲 | 多赛季合并已修(position 1-9 序列,非全 position=1)。**但休赛期空壳陷阱未修**:意甲返 2026-27 预建空壳(20 队全 0 分),应取 2025-26 真实赛季(见新问题 2) | ⚠️ |
| A18 | ⚠️ tool_logic_gap(同 A10) | get_standings(168) 荷甲 | 返 2025-26 赛季(13272)真实积分榜:埃因霍温 84 分 pos1/费耶诺德 65 pos2/奈梅亨 59 pos3...数据完整。荷甲无 2026-27 空壳,season 选择命中真实赛季 | ✅ |
| H06 | ⚠️ implementation_gap(promotion_id 已编码但工具未暴露) | get_standings(82) 英超看 promotion_id 字段 | 返回行含 `promotion_id` 字段(205=欧冠/206=欧联/0=无)。**但休赛期空壳陷阱未修**:英超返 2026-27 空壳(20 队全 0 分),promotion_id 是预置值非真实赛季结果(见新问题 2) | ⚠️ |
| F03 | ⚠️ implementation_gap(篮球 id 碰撞伪命中足球) | get_odds_trend(3911714, sport="basketball") | 返篮球 2-way 赔率(home_win 1.800/away_win 1.910/draw 0.000),changed_at=1782613516(2026-06-28),与 v2 SQL 基准一致。不再伪命中 2023 足球 1X2。篮球年分区表路由生效 | ✅ |

### 升档统计

**5 ✅ / 4 ⚠️ / 0 ❌**

- ✅: E05, B04, E10, A18, F03
- ⚠️: E07, D05, A10, H06
- ❌: 无

## 二、各场景验证详情

### E05 — 合成 ID 假命中 ✅

v2 撞墙:`get_lottery_schedule(401)` 返回 `match_id=260891`(合成 ID,形如 issue*10+match_no),与历史 football_match.id 碰撞(260891→2009 法低级联赛),下游 `get_odds_snapshot(260891)=SKIP_MATCH`。

重写后实跑 `get_lottery_schedule(401, period=26089)` 前 3 条:
```
lottery_official_id=260891, football_match_id=4459720, match_id=4459720  (巴西vs日本)
lottery_official_id=260892, football_match_id=4459718, match_id=4459718  (德国vs巴拉圭)
lottery_official_id=260893, football_match_id=4459719, match_id=4459719  (荷兰vs摩洛哥)
```
合成 ID 与真实 ID 已分离,`match_id` 字段指向真实 football_match.id(4459720 系列,与 v2 SQL 基准完全一致)。JOIN lottery_match 回填正确。**升档 ✅**。

### E07 / D05 — 北单 bf JSON 解析 ⚠️

v2 撞墙:`_parse_lottery_play` 按逗号硬切 JSON,返回 `bf=[{label:"2:0",odds:"{\"s30\":\"32.38\""},...]`(截断碎片 + label↔key 错位)。

重写后实跑 `get_lottery_schedule(301)` 北单 issue 26071:
```
bf: [{label:"3:1",odds:33.4},{label:"3:0",odds:83.26},{label:"1:1",odds:7.95},...,{label:"2:0",odds:31.33},...]
```
bf 字段已是结构化 `[{label,odds}]` 列表,JSON 解析修复生效。**bf 维度升档 ✅**。

**但 spf 字段语义错位(新发现问题)**:
- DB 原始 JSON: `{"sf3":"4.02","goal":"0","sf0":"2.16","sf1":"3.44"}`
- 工具返回: `{"handicap":0.0, "win":3.44, "draw":null, "loss":4.02}`
- 正确语义(依据 v2 E07 证据 sf3=主胜/sf1=让球平/sf0=客胜): win=4.02(sf3)/draw=3.44(sf1)/loss=2.16(sf0)
- 实际: win=3.44(sf1 让球平)/draw=null(sf2 不存在)/loss=4.02(sf3 主胜) → **win 与 loss 互换、draw 丢失**

`_parse_beidan_play` 的 spf 分支映射错误(`win=sf1/draw=sf2/loss=sf3` 应为 `win=sf3/draw=sf1/loss=sf0`)。bf/jq/bqc/sxp 解析正确,仅 spf 错位。

D05 的比分玩法路由澄清:v2 用 404(让球胜平负)取 bf,但 404 表只含 sf 不含 bf;bf 在 301(胜负过关)表。当前 301 已正确 surface bf。**E07/D05 因 spf 语义错位判 ⚠️**,bf 修复部分达标。

### B04 — 无 date 时被青年/女足占满 ✅

v2 撞墙:`resolve_match(中国,日本)` 无 date 时返 10 候选全为 U17/U20/U23/女足,唯一男子 A 级 4146376 排第 10,SQL 基准 TOP 4334205 被截断。

重写后实跑 `resolve_match(中国,日本,national=True)`:
```
首选选 match_id=4146376 中国(11087)vs 日本(14529) 世亚预 2024-11-19 status=finished
```
男子国家队 A 级置顶,U17/U20/U23/女足全排除。`national=True` + `exclude_youth` 过滤生效。**升档 ✅**。

残留:候选第 2 位是 3898055 中国沙滩足球队 vs 日本沙滩足球队(2023 沙滩世杯),因 youth_patterns 未含 "%沙滩%"/"%室内%"/"%U24%"。不影响首选正确性,但候选洁净度有瑕(见新问题 3)。

### E10 — resolve_team("日本")返回 U 系列 ✅

v2 撞墙:`resolve_team("日本")` 10 候选全为明星队/U16~U21/女足,14529(成年国家队)不在 top-10。

重写后实跑 `resolve_team(日本,national=True)`:
```
首选 team_id=14529 日本成年国家队 national=1
其余: 日本沙滩足球队(19631)/日本室内足球队(20515)/日本U24(60415)
```
14529 置顶,主修复达成。**升档 ✅**。

残留:沙滩/室内/U24 仍混入(见新问题 3),但成年国家队排首位,LLM 可直接选用。

### A10 — 意甲多赛季合并 ⚠️

v2 撞墙:`get_standings(108)` 返 30 行全 position=1(国米 84/94/97 三次重复),缺 season_id 过滤。

重写后实跑 `get_standings(108)`:
```
competition_type=1 (league)
rows: 20 行 position 1-20,但全部 points=0/played=0/won=0...
```
多赛季合并已修(position 序列 1-20,非全 1)。**但 season_id 选择命中 2026-27 空壳**:

DB 实测意甲 108 season_id 分布:
| season_id | year | is_current | team_rows | played_rows |
|-----------|------|------------|-----------|-------------|
| 14222 | 2026-2027 | 1 | 20 | **0** (空壳) |
| 13238 | 2025-2026 | 0 | 20 | 20 (真实) |

重写 SQL `MAX(season_id) WHERE has team rows` 命中 14222(空壳有 team_rows 但 played=0)。应加 `pt2.total>0` 过滤取 13238。**判 ⚠️**:多赛季合并修复 ✅,休赛期空壳陷阱未修 ⚠️。

### A18 — 荷甲 season_id 选择 ✅

v2 撞墙:同 A10,get_standings(168) 缺 season_id 过滤。

重写后实跑 `get_standings(168)`:
```
competition_type=1 (league)
pos1 埃因霍温 84分(27胜3平4负,34轮,进101失45,promotion_id=205 欧冠)
pos2 费耶诺德 65分(promotion_id=205)
pos3 奈梅亨 59分(promotion_id=169 欧冠资格)
...
```
DB 实测荷甲 168 season_id 分布:MAX(13272, 2025-26, 18 played_rows)=真实赛季,无 2026-27 空壳。season 选择命中真实数据。**升档 ✅**。

### H06 — 英超 promotion_id 暴露 ⚠️

v2 撞墙:get_standings 返回结构丢弃 promotion_id,欧战赛区标签需 SQL JOIN。

重写后实跑 `get_standings(82)`:
```
rows[0]: team_name=阿森纳, position=1, points=0, played=0, promotion_id=205, promotion_name=null
rows[1]: team_name=阿斯顿维拉, position=2, points=0, promotion_id=205
...
```
**promotion_id 字段已暴露 ✅**(205 欧冠/206 欧联/0 无)。但 `promotion_name=null`(JOIN football_promotions 未实现,只透传 id)。且同样命中 2026-27 空壳(20 队全 0 分),promotion_id 是预置值非真实赛季结果。

DB 实测英超 82 season_id 分布:
| season_id | year | is_current | team_rows | played_rows |
|-----------|------|------------|-----------|-------------|
| 14320 | 2026-2027 | 1 | 20 | **0** (空壳) |
| 13242 | 2025-2026 | 0 | 20 | 20 (真实) |

按任务验证标准("看返回是否含 promotion_id 字段")→ 含,**字段层面 ✅**;但 season_id 陷阱使数据为空壳预置,**实际可用性 ⚠️**。综合判 ⚠️:promotion_id 暴露达标,season_id 陷阱未修 + promotion_name 未填充。

### F03 — 篮球 get_odds_trend 伪命中 ✅

v2 撞墙:`get_odds_trend(3911714)` 硬编码 football_match,返 2023 足球 1X2(1.59/3.42/5.27),与 2026 篮球真实数据(2-way 1.80/1.91)错位。

重写后实跑 `get_odds_trend(3911714, sport="basketball")`:
```
[{home_win:"1.800", draw:"0.000", away_win:"1.910", changed_at:1782613516, company:"12bet/沙巴"},
 {home_win:"1.840", draw:"0.000", away_win:"1.940", changed_at:1782613516, company:"立博"},
 {home_win:"1.730", draw:"0.000", away_win:"1.830", changed_at:1782613518, company:"onex"}]
```
2-way 篮球赔率(无和局),changed_at=1782613516=2026-06-28,与 v2 SQL 基准完全一致。篮球年分区表 `basketball_odds_europe_change_2026` 路由生效,不再伪命中足球。**升档 ✅**。

## 三、新发现的问题

### 问题 1:北单 spf 语义映射错位(P1,tool_logic_gap)

**位置**:`foretell/tools/crazy_sports/mysql_client.py:2422-2428` `_parse_beidan_play` 的 spf 分支

**现状**:
```python
if play_key == "spf":
    return {
        "handicap": _safe_float(data.get("goal")),
        "win": _safe_float(data.get("sf1")),
        "draw": _safe_float(data.get("sf2")),
        "loss": _safe_float(data.get("sf3")),
    }
```

**DB 原始 JSON 实测**:`{"sf3":"4.02","goal":"0","sf0":"2.16","sf1":"3.44"}`
- sf3=主胜=4.02、sf1=让球平=3.44、sf0=客胜=2.16(依据 v2 E07 证据 "spf.sf3=2.22=主胜"、D05 "spf.sf3=2.74=主胜")

**正确映射应为**:`win=sf3(4.02) / draw=sf1(3.44) / loss=sf0(2.16)`

**当前错位**:win=sf1(3.44 让球平) / draw=sf2(null 不存在) / loss=sf3(4.02 主胜) → win↔loss 互换、draw 丢失

**影响**:E07/D05 及所有北单 301 玩法的 spf 字段 win/loss 互换、draw 丢失,生产环境会给出反过来的胜负赔率。bf/jq/bqc/sxp 不受影响。

**建议修复**:
```python
return {
    "handicap": _safe_float(data.get("goal")),
    "win": _safe_float(data.get("sf3")),
    "draw": _safe_float(data.get("sf1")),
    "loss": _safe_float(data.get("sf0")),
}
```

### 问题 2:get_standings season_id 选择未过滤 played_rows>0(P2,tool_logic_gap 残留)

**位置**:`foretell/tools/crazy_sports/mysql_client.py:1007-1013` get_standings 的 season 选择子查询

**现状**:取 `MAX(season_id) WHERE EXISTS team_rows`,但新赛季预建空壳也有 team_rows(0 分)。

**DB 实测**:
- 意甲 108:season 14222(2026-27 空壳,20 team_rows,0 played)被选中,应选 13238(2025-26 真实)
- 英超 82:season 14320(2026-27 空壳)被选中,应选 13242(2025-26 真实)
- 荷甲 168:无 2026-27 空壳,MAX(13272)恰好真实 → A18 通过

**影响**:休赛期(6-7 月)查询五大联赛积分榜返 0 分空壳,A10/H06 残留 ⚠️。荷甲等未预建空壳的联赛不受影响。

**建议修复**:season 选择子查询加 `pt2.total > 0` 过滤:
```sql
SELECT MAX(p2.season_id) FROM football_points_table p2
JOIN football_points_table_team pt2 ON pt2.table_id = p2.id
WHERE p2.competition_id = %s AND pt2.total > 0
```

### 问题 3:resolve_team/resolve_match 未排除沙滩/室内/U24(P3,残留)

**位置**:`foretell/tools/crazy_sports/mysql_client.py:512-515, 589-592` youth_patterns

**现状**:youth_patterns 含 U15-U23/青年/女足/预备队,但缺 `%沙滩%`/`%室内%`/`%futsal%`/`%beach%`/`%U24%`。

**实测**:
- `resolve_team(日本,national=True)` 返候选含 日本沙滩足球队(19631)/日本室内足球队(20515)/日本U24(60415)
- `resolve_match(中国,日本,national=True)` 候选第 2 位是中国沙滩 vs 日本沙滩

**影响**:成年国家队仍置顶(主修复达成),但候选洁净度有瑕,LLM 需额外判断排除沙滩/室内。U24 是新出现的 U 系列编号(巴黎奥运周期遗留),原 patterns 未覆盖。

**建议修复**:youth_patterns 追加 `"%U24%"`、`"%沙滩%"`、`"%室内%"`、`"%futsal%"`、`"%beach%"`。

### 问题 4:promotion_name 未填充(P3,残留)

**位置**:`_format_standings_row` 透传 `promotion_name` 但 SQL 未 JOIN football_promotions

**现状**:H06 实测 `promotion_id=205, promotion_name=null`。id 已暴露但赛区名(欧冠正赛/欧联正赛/欧协联资格赛)未填充,LLM 需外部知识映射 205=欧冠。

**建议修复**:get_standings SQL `LEFT JOIN football_promotions pr ON pt.promotion_id = pr.id`,select `pr.name AS promotion_name`。

## 四、对 s3e 剩余域(deep sport/schedule/player)的建议

1. **deep sport 域**(get_match_half_stats/get_match_team_stats 等):
   - 注意 sport 参数路由,参考 F03 篮球分支修复模式:不要硬编码 `football_match`,按 sport 路由到 `basketball_match` + 对应统计表
   - 篮球统计表分区/字段语义可能与足球不同,需先查 information_schema 确认

2. **schedule 域**(get_team_schedule/get_schedule_by_date):
   - 注意 season_id 选择陷阱,参考 A10/H06 残留:取"有 played 数据的最近赛季"而非 MAX(season_id),避免休赛期空壳
   - get_team_schedule 当前用 match_time DESC,无 season 过滤,跨赛季可能混淆;可考虑加 season_id 可选参数

3. **player 域**(resolve_player/get_player_stats 等):
   - 注意 youth 排除模式补全:参照新问题 3,resolve_player 若按队名模糊查可能也命中青年队球员,需同步追加 U24/沙滩/室内 patterns
   - 球员 nationality/position 消歧可能需类似 national 参数的显式过滤

4. **通用建议**:
   - season_id 选择逻辑应统一抽成 helper(get_latest_played_season(competition_id)),避免每个 standings/stats 工具各自踩空壳陷阱
   - 北单/竞彩 JSON 字段解析应继续按彩种分支,但需对照 nami_field_map_full.yaml 校验每个 play_key 的 key 语义(本次 spf 错位即因未校验 sf0/sf1/sf3 语义)
   - 所有"JOIN 关联表回填真实 ID"的修复(E05/E07 模式)应在 deep sport/schedule/player 域复用,避免合成 ID 假命中

## 五、结论

阶段 3 第一批重写**部分达标**:5/9 升档 ✅,4/9 残留 ⚠️(无 ❌)。核心修复方向正确:
- lottery 合成 ID 分离(E05)✅、bf JSON 解析(E07/D05)✅
- entity national 过滤(B04/E10)✅
- standings 多赛季合并修复(A10/A18)✅、promotion_id 暴露(H06)✅
- odds 篮球路由(F03)✅

残留 4 个 ⚠️ 均为"主修复达成但相邻维度有瑕":
- E07/D05:bf 修好但 spf 语义错位(新问题 1,P1 需立即修)
- A10/H06:多赛季合并修好但休赛期空壳陷阱(新问题 2,P2)
- B04/E10:虽判 ✅ 但沙滩/室内/U24 残留(新问题 3,P3)

建议下批重写优先级:**问题 1(spf 语义)> 问题 2(season 空壳)> 问题 3(youth patterns 补全)> 问题 4(promotion_name JOIN)**。
