# Foretell LLM Eval v2 — H 场景批次汇总(8 类型)

执行时间:2026-06-29
方法论:**LLM 自主判断**(沿用前批次)。H 场景为 league/competition 维度语义精度场景。

## 一、总表

| type_id | 名称 | 分类 | 关键发现 |
|---|---|---|---|
| H01 | 争冠悬念 | ✅ | **get_standings season_id 语义gap**:休赛期按MAX(season_id)取到未开打新赛季返回空榜,SQL指定season_id=13242取真实终榜(阿森纳85分夺冠);争冠悬念是合成语义无专用工具 |
| H02 | 降级确定 | ✅ | resolve_league("韩职")别名未收录fallback"韩K联"→581;get_standings 12队完整+SQL max_round=33已踢15轮剩18轮;降级判定合成(光州FC 7分理论最高61>安全线14);atomic文案与type_name错配 |
| H03 | 季后赛锁定 | ✅ | **get_basketball_standings支持NBA但有缺陷**:未按scope过滤混排季前赛/常规赛/杯赛,conference字段返回战绩非分区名,需SQL WHERE p.scope=5兜底;**无篮球赛程工具**(get_team_schedule硬编码football);SQL scope=5+bracket_match_up双重验证东西部前8 |
| H04 | 冠军已锁定 | ✅ | **样本选择陷阱**:6月底避开MAX(season_id)空榜联赛(英超/意甲),西甲(120)仍保留完赛积分榜且future_cnt=0是干净样本(巴萨94领先皇马8,remaining=0,8>0×3成立);无原生工具由standings+总轮次合成lead>remaining×3;atomic T1-a1.target.entity误标match |
| H05 | 保级形势 | ⚠️ | 工具层无问题(get_standings完整);**context_gap时点陷阱**:2026-06-29赛季间歇期西甲/德甲满轮无upcoming,"保级形势"退化为"降级定局","剩余轮次+赛程难度"维度为0/N/A,换赛季中时点同路径可完整回答;atomic文案错配 |
| H06 | 欧战席位 | ✅ | **重大发现:欧战资格规则由DB直接编码**(football_points_table_team.promotion_id JOIN football_promotions给出赛区:英超205欧冠1-5/206欧联6-7/172欧协联8;瑞典超169欧冠资格/172欧协联资格),消除knowledge_gap;get_standings season_id陷阱+丢弃promotion_id,SQL workaround;活态联赛瑞典超直接可用 |
| H07 | 世界杯进程 | ✅ | resolve_league(世界杯→1)+get_seasons(13776)+SQL football_stage(7阶段)+match按stage×status分组;**当前世界杯进行到1/16决赛**(小组赛72场全完赛,1/16今日1场完赛余15场6/30起);**football_stage表无"当前轮"标识**需JOIN match按status_id+match_time判定;eval夹具矛盾(文案"中乙"配type_name"世界杯进程") |
| H08 | 数学出线 | ✅ | 6场世界杯全resolve_match OK(西班牙vs沙特4460924第8组第2轮、德国vs科特迪瓦4460915第5组第2轮);文案4个历史交锋典故h2h全真实可查;**文案模板数字大量硬编与DB不符**(西班牙"7胜3平"实6胜4平、伊朗"3胜1平1负狂轰11球"实2胜3平进8丢4等),LLM重写应弃模板不符数字;SQL按group拿完整4队榜验证出线 |

**分类统计**:
- ✅ 找到可行路径:**7 个**(H01,H02,H03,H04,H06,H07,H08)
- ⚠️ 找到路径但有隐患:**1 个**(H05)
- ❌ 穷尽探索后确认无解:**0 个**

## 二、关键洞察

1. **H 场景语义精度工具链基本成熟**:8 个场景 7/8 干净通过,league/competition 维度的 get_standings/get_seasons/resolve_league + SQL football_stage/football_points_table/promotions 组合可覆盖争冠/降级/保级/欧战/冠军锁定/世界杯进程/数学出线全部语义。

2. **get_standings season_id 陷阱是 H 场景最高频问题**:H01/H04/H06 均报告 6 月底休赛期按 MAX(season_id) 取到未开打新赛季空榜,需 SQL 指定具体 season_id fallback。这是 P3 优先修复项(影响所有休赛期联赛场景)。

3. **重大发现:欧战资格规则由 DB 直接编码**(H06):football_points_table_team.promotion_id JOIN football_promotions 给出各联赛欧战赛区名称,消除了"欧战资格规则需外部知识"的 knowledge_gap。这是 Phase 2 工具层未暴露的重要数据,DB 已有完整编码。

4. **get_basketball_standings scope 过滤缺陷**(H03):未按 basketball_points_table.scope 过滤,混排季前赛/常规赛/杯赛,需 SQL WHERE p.scope=5 兜底。**无篮球赛程工具**:get_team_schedule 硬编码 football_match 不支持篮球,中赛季"锁定"场景缺剩余场次维度。

5. **football_stage 表无"当前轮"标识**(H07):"打到哪一轮"必须 JOIN football_match 按 status_id+match_time 综合判定,无专用工具。

6. **H 场景 atomic 文案生成缺陷**:H02/H04/H05/H06/H07 多个场景 atomic 文案与 type_name/entity_entry 语义错配(如 H07 文案"中乙"配 type_name"世界杯进程"),target.entity 误标 match(应为 league)。这是 eval 夹具生成问题,不影响路径探索(按 type_name 真实语义探路)。

7. **H08 文案模板数字硬编与 DB 不符**:模板自身数字大量不可信(与文案"没查到的数据别硬编"矛盾),LLM 重写应弃模板不符数字改用 DB 真实数据,验证了 foretell 工具链对"数据真实性核验"的支撑能力。

## 三、产出文件
- data/eval/path_attempts/H01-H08.yaml(8 个)
- data/eval/batch_H_summary.md(本文件)
