"""One-shot generator for data/eval/taxonomy.yaml (120 types). Run: uv run python scripts/_gen_taxonomy.py"""

from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "eval" / "taxonomy.yaml"


def _types() -> list[dict]:
    types: list[dict] = []

    def add(
        id_: str,
        scenario: str,
        name: str,
        description: str,
        *,
        entity_entry: str = "unknown",
        sport: str = "any",
        complexity: str = "medium",
        patterns: list[str] | None = None,
        keywords: list[str] | None = None,
        priority: int = 50,
        tags: list[str] | None = None,
    ) -> None:
        types.append(
            {
                "id": id_,
                "scenario": scenario,
                "name": name,
                "description": description,
                "entity_entry": entity_entry,
                "sport": sport,
                "complexity": complexity,
                "patterns": patterns or [],
                "keywords": keywords or [],
                "priority": priority,
                "tags": tags or [],
            }
        )

    # A 轻量查询 A01-A18
    add("A01", "A", "按日期热门赛程", "今日/今晚五大联赛或NBA热门赛程", entity_entry="date", patterns=[r"今晚.*(五大联赛|NBA|足球|篮球|比赛)", r"今天.*有什么.*比赛", r"今日.*赛程"], priority=80, tags=["schedule", "date"])
    add("A02", "A", "指定联赛日期赛程", "某日某联赛全部比赛", entity_entry="date+league", patterns=[r"(英超|西甲|意甲|德甲|法甲|欧冠|中超).*(今天|今晚|明天|赛程)", r"(今天|今晚|明天).*(英超|西甲|意甲|德甲|法甲|欧冠)"], priority=78)
    add("A03", "A", "球队未来赛程", "某队接下来打谁", entity_entry="team", patterns=[r"(接下来|未来|下场|后面).*(打|踢|对阵|比赛)", r".*(接下来打谁|接下来.*赛程)"], priority=85, tags=["schedule", "team"])
    add("A04", "A", "球队近期赛程", "某队最近几场", entity_entry="team", patterns=[r"(最近|近)\d*场", r".*最近.*(赛程|比赛|对阵)"], priority=75)
    add("A05", "A", "实时比分查询", "进行中比赛比分", entity_entry="match", patterns=[r"实时比分", r"(现在|目前|当前).*(比分|几比几)", r"比分多少"], priority=70)
    add("A06", "A", "完场赛果", "已结束比赛结果", entity_entry="match", patterns=[r"完场|赛果|最终结果|比分结果", r"昨天.*(比分|结果)"], priority=72)
    add("A07", "A", "时间窗_今晚", "今晚是否有某队比赛", entity_entry="team+time", sport="football", complexity="high", patterns=[r"今晚.*(比赛|开始|踢|赛)", r"今晚的.*"], priority=88, tags=["time_window"])
    add("A08", "A", "时间窗_明早", "明早/凌晨场次", entity_entry="team+time", complexity="high", patterns=[r"明早|明天早上|明天.*(世界杯|比赛|开始)", r"凌晨.*场"], priority=90, tags=["time_window", "regression"])
    add("A09", "A", "时间窗_几点开赛", "开赛时间查询", entity_entry="team+time", patterns=[r"什么时候开始|几点开|开球时间|几点踢"], priority=86)
    add("A10", "A", "积分榜", "联赛积分排名", entity_entry="league", patterns=[r"积分榜|积分表|积分排名"], priority=82)
    add("A11", "A", "射手榜", "球员进球榜", entity_entry="league", patterns=[r"射手榜|进球榜|金靴"], priority=80)
    add("A12", "A", "球队赛季统计", "球队进失球等赛季数据", entity_entry="team", patterns=[r"本赛季.*(进|失|数据|统计|战绩)", r".*进了多少球"], priority=78)
    add("A13", "A", "历史交锋", "两队历史对战", entity_entry="team_pair", patterns=[r"历史交锋|交手记录|对战记录|交锋战绩"], priority=80)
    add("A14", "A", "球队阵容", "大名单/阵容", entity_entry="team", patterns=[r"阵容|大名单|球员名单"], priority=76)
    add("A15", "A", "比赛首发", "单场首发阵容", entity_entry="match", patterns=[r"首发阵容|首发名单|预计首发"], priority=74)
    add("A16", "A", "NBA赛程", "NBA球队或日期赛程", entity_entry="team", sport="basketball", patterns=[r"NBA.*(赛程|比赛|对阵)", r"(湖人|勇士|凯尔特人|雷霆|掘金|热火).*(赛程|比赛|对阵)"], priority=84)
    add("A17", "A", "实体消歧_国家队", "国家队vs俱乐部消歧", entity_entry="team", complexity="high", patterns=[r"(男足|女足|国家队|U21|俱乐部)", r"法国.*世界杯|葡萄牙.*世界杯"], priority=92, tags=["disambiguation"])
    add("A18", "A", "语义精度_锁定排名", "锁定精确名次vs下限", entity_entry="league", complexity="high", patterns=[r"锁定.*(冠军|降级|季后赛|排名)", r"已经降级|已经夺冠|还有悬念"], priority=88, tags=["semantic"])

    # B 单场深度 B01-B16
    add("B01", "B", "竞彩模板分析", "竞彩足球周X00X标准模板", entity_entry="lottery_code", sport="football", complexity="high", patterns=[r"分析【.*竞彩足球周[一二三四五六日]\d{3}"], priority=95, tags=["lottery_template"])
    add("B02", "B", "竞彩篮球模板", "竞彩篮球编号分析", entity_entry="lottery_code", sport="basketball", patterns=[r"竞彩篮球.*周[一二三四五六日]\d{3}", r"分析【.*竞彩篮球"], priority=93)
    add("B03", "B", "对阵加日期分析", "A VS B + 日期", entity_entry="match_pair", patterns=[r"分析.*\d{4}-\d{2}-\d{2}.*VS", r"\d{4}-\d{2}-\d{2}.*VS.*分析"], priority=88)
    add("B04", "B", "对阵无日期分析", "仅两队名称深度分析", entity_entry="match_pair", patterns=[r"分析.*VS", r".*VS.*(分析|预测|怎么样)"], priority=86)
    add("B05", "B", "谁会赢", "简短胜负预测", entity_entry="match_pair", patterns=[r"谁会赢|能赢吗|胜负走向|赢面"], priority=84)
    add("B06", "B", "全面深度分析", "六段式完整分析", entity_entry="match", patterns=[r"全面分析|深度分析|详细分析|六段"], priority=87)
    add("B07", "B", "自定义模板", "用户指定输出结构", entity_entry="match", patterns=[r"按.*模板|主队一段|四步稳球|自定义"], priority=80)
    add("B08", "B", "篮球五段分析", "NBA单场深度", entity_entry="match", sport="basketball", patterns=[r"(NBA|篮球).*(分析|预测).*(让分|大小分)"], priority=85)
    add("B09", "B", "系列赛G7", "季后赛G7约束", entity_entry="match", sport="basketball", complexity="high", patterns=[r"\bG7\b|抢七|第七场|系列赛第"], priority=94, tags=["series"])
    add("B10", "B", "淘汰赛排名不适用", "杯赛淘汰赛问联赛排名", entity_entry="match", complexity="high", patterns=[r"世界杯.*排名|淘汰赛.*积分"], priority=82)
    add("B11", "B", "盘口不足跳过", "数据不足应跳过", entity_entry="match", complexity="high", patterns=[r"盘口.*不足|数据不足.*跳过|建议跳过"], priority=78)
    add("B12", "B", "换线重定价", "初盘即时盘换线", entity_entry="match", patterns=[r"换线|重定价|已换盘"], priority=76)
    add("B13", "B", "伤病结合分析", "伤病+状态+盘口", entity_entry="match", patterns=[r"结合伤病", r"伤病名单.*影响"], priority=89)
    add("B14", "B", "进球数深度", "总进球/大小球分析", entity_entry="match", patterns=[r"进球数.*分析|大小球.*分析|总进球"], priority=83)
    add("B15", "B", "半全场分析", "半全场玩法分析", entity_entry="match", patterns=[r"半全场"], priority=81)
    add("B16", "B", "实力对比", "两队实力对比无明确购彩", entity_entry="match_pair", patterns=[r"实力对比|实力分析|谁更强"], priority=79)

    # C 复盘 C01-C08
    add("C01", "C", "昨天比赛复盘", "昨日赛果回顾", entity_entry="match", patterns=[r"昨天.*(怎么回事|复盘|回顾|那场)"], priority=80)
    add("C02", "C", "上周比赛复盘", "相对时间复盘", entity_entry="match", patterns=[r"上周|上一场.*(复盘|回顾)"], priority=78)
    add("C03", "C", "对阵复盘", "队名对阵复盘", entity_entry="match_pair", patterns=[r"复盘.*VS|回顾.*VS"], priority=82)
    add("C04", "C", "竞彩编号复盘", "按编号复盘", entity_entry="lottery_code", patterns=[r"复盘.*周[一二三四五六日]\d{3}"], priority=84)
    add("C05", "C", "篮球复盘", "NBA赛后回顾", entity_entry="match", sport="basketball", patterns=[r"(NBA|篮球).*复盘"], priority=80)
    add("C06", "C", "焦点战回顾", "焦点战/重要比赛回顾", entity_entry="match", patterns=[r"焦点战.*回顾|重要.*回顾"], priority=76)
    add("C07", "C", "近期战绩复盘", "球队近期表现回顾", entity_entry="team", patterns=[r"近期战绩复盘|最近.*战绩.*复盘"], priority=74)
    add("C08", "C", "欧冠复盘", "欧冠场次复盘", entity_entry="match", patterns=[r"欧冠.*复盘"], priority=78)

    # D 购彩 D01-D10
    add("D01", "D", "这场怎么买", "单场购彩方案", entity_entry="match", patterns=[r"怎么买|如何买|这场.*买"], priority=88)
    add("D02", "D", "主不败推荐", "主不败/不败推荐", entity_entry="match", patterns=[r"主不败|不败可以吗|主队不败"], priority=86)
    add("D03", "D", "让球推荐", "让球胜平负推荐", entity_entry="match", patterns=[r"让球.*(推荐|买|方案|能赢)"], priority=84)
    add("D04", "D", "大小球推荐", "大小球/进球数推荐", entity_entry="match", patterns=[r"大小球|大分小分|大\d|小\d|总进球.*(推荐|买)"], priority=84)
    add("D05", "D", "比分玩法", "比分投注建议", entity_entry="match", patterns=[r"比分.*(推荐|买|方案|串)"], priority=82)
    add("D06", "D", "单场方案", "明确要方案", entity_entry="match", patterns=[r"单场方案|给个方案|赛事方案"], priority=85)
    add("D07", "D", "篮球让分购彩", "NBA让分投注", entity_entry="match", sport="basketball", patterns=[r"让分.*(能赢|推荐|买)"], priority=86)
    add("D08", "D", "胜平负推荐", "胜平负明确推荐", entity_entry="match", patterns=[r"胜平负.*(推荐|买|倾向)"], priority=83)
    add("D09", "D", "稳胆推荐", "稳胆/稳场", entity_entry="match", patterns=[r"稳胆|稳场|稳赢"], priority=80)
    add("D10", "D", "购彩风险提示", "需含风险声明", entity_entry="match", complexity="high", patterns=[r"推荐.*串|方案.*串"], priority=75, tags=["disclaimer"])

    # E 批量 E01-E14
    add("E01", "E", "扫盘", "批量初筛", entity_entry="lottery_batch", patterns=[r"扫盘|扫一下|帮我扫"], priority=90)
    add("E02", "E", "四串一", "四串一方案", entity_entry="lottery_batch", patterns=[r"四串一|4串1"], priority=92)
    add("E03", "E", "三串一", "三串一方案", entity_entry="lottery_batch", patterns=[r"三串一|3串1|3串一"], priority=91)
    add("E04", "E", "二串一", "二串一方案", entity_entry="lottery_batch", patterns=[r"二串一|2串1|2串一"], priority=90)
    add("E05", "E", "十四场", "胜负彩十四场", entity_entry="lottery_period", patterns=[r"十四场|胜负彩"], priority=93)
    add("E06", "E", "任九", "任选九场", entity_entry="lottery_period", patterns=[r"任九|任选.*9"], priority=92)
    add("E07", "E", "北单", "北京单场", entity_entry="lottery_batch", patterns=[r"北单"], priority=88)
    add("E08", "E", "今日竞彩列表", "今日可售竞彩场次", entity_entry="date", patterns=[r"今天竞彩|今日竞彩|竞彩.*有哪些"], priority=86)
    add("E09", "E", "批量世界杯", "多场世界杯一起分析", entity_entry="batch", complexity="high", patterns=[r"(四场|多场|接下来.*场).*世界杯", r"世界杯.*(四场|多场)"], priority=94)
    add("E10", "E", "初筛vs深核", "初筛后深度核验", entity_entry="batch", complexity="high", patterns=[r"重新深度分析|综合.*后再给|深度核验"], priority=88)
    add("E11", "E", "比分串方案", "比分串关", entity_entry="batch", patterns=[r"比分串"], priority=87)
    add("E12", "E", "在售方案", "引用已发布方案", entity_entry="batch", patterns=[r"在售方案|你发布的.*方案"], priority=85)
    add("E13", "E", "推荐N场", "推荐多场靠谱场次", entity_entry="batch", patterns=[r"推荐\d场|推荐.*场.*靠谱"], priority=84)
    add("E14", "E", "竞篮今日", "今日竞彩篮球场次", entity_entry="date", sport="basketball", patterns=[r"竞篮|竞彩篮球.*(今天|有哪些)"], priority=86)

    # F 赔率 F01-F10
    add("F01", "F", "赔率对比", "多家公司快照对比", entity_entry="match", patterns=[r"赔率对比|对比.*赔率|各家赔率"], priority=88)
    add("F02", "F", "赔率走势", "赔率变化追踪", entity_entry="match", patterns=[r"赔率.*(变化|走势|变动|升降)"], priority=90)
    add("F03", "F", "变动最大", "当日赔率变动排名", entity_entry="date", patterns=[r"变动最大|变化最大.*赔率"], priority=84)
    add("F04", "F", "凯利指数", "凯利查询", entity_entry="match", patterns=[r"凯利"], priority=86)
    add("F05", "F", "赔率时间线", "完整赔率历史", entity_entry="match", patterns=[r"赔率.*时间线|历史赔率"], priority=82)
    add("F06", "F", "盘口解读", "亚盘/让球盘口", entity_entry="match", patterns=[r"盘口.*(解读|分析|怎么看)"], priority=85)
    add("F07", "F", "临场盘口", "临场水位变化", entity_entry="match", patterns=[r"临场|即时盘"], priority=83)
    add("F08", "F", "现在盘口", "追问当前盘口", entity_entry="match", patterns=[r"现在盘口|现在是.*加\d|盘口是"], priority=87, tags=["follow_up"])
    add("F09", "F", "水位方向", "水位与盘口一致性", entity_entry="match", patterns=[r"水位|上盘|下盘"], priority=80)
    add("F10", "F", "欧赔亚盘", "欧赔亚盘联合", entity_entry="match", patterns=[r"欧赔.*亚盘|亚盘.*欧赔"], priority=81)

    # G 多轮 G01-G20
    add("G01", "G", "比分预测追问", "分析后比分预测", entity_entry="context", complexity="high", patterns=[r"^比分预测$|^预测比分$"], priority=98, tags=["follow_up"])
    add("G02", "G", "率先进球追问", "先进球概率", entity_entry="context", complexity="high", patterns=[r"率先进球|先进球"], priority=98, tags=["follow_up"])
    add("G03", "G", "各比分概率", "比分矩阵", entity_entry="context", complexity="high", patterns=[r"各比分|比分概率|比分之间的概率"], priority=97, tags=["follow_up"])
    add("G04", "G", "上半场进球概率", "时段概率", entity_entry="context", complexity="high", patterns=[r"上半场.*进球|时段.*概率"], priority=96, tags=["follow_up"])
    add("G05", "G", "继续", "短追问继续", entity_entry="context", patterns=[r"^继续$"], priority=95, tags=["follow_up"])
    add("G06", "G", "复述原文", "原样再发", entity_entry="context", patterns=[r"原样.*发|再发一遍|刚才.*再"], priority=94, tags=["follow_up"])
    add("G07", "G", "优化方案", "优化先前输出", entity_entry="context", patterns=[r"优化|改进.*方案|再综合"], priority=93, tags=["follow_up"])
    add("G08", "G", "同样逻辑", "沿用上一轮逻辑", entity_entry="context", complexity="high", patterns=[r"同样逻辑|同样.*分析|一样的逻辑"], priority=96, tags=["follow_up", "context"])
    add("G09", "G", "换场追问", "同会话换一场比赛", entity_entry="context", complexity="high", patterns=[r"呢$|这场呢|那边呢"], priority=85, tags=["follow_up"])
    add("G10", "G", "重新分析", "要求重新深度分析", entity_entry="context", patterns=[r"重新分析|再分析|重新深度"], priority=92, tags=["follow_up"])
    add("G11", "G", "用户纠正", "用户纠正系统误解", entity_entry="context", complexity="high", patterns=[r"不对|你搞错|明明是|我说的是"], priority=97, tags=["regression"])
    add("G12", "G", "时间窗纠正", "纠正时间理解", entity_entry="context", complexity="high", patterns=[r"明天早上.*世界杯|今晚.*世界杯"], priority=98, tags=["regression", "time_window"])
    add("G13", "G", "进球数追问", "深度分析进球数", entity_entry="context", patterns=[r"^进球数$|进球数深度"], priority=90, tags=["follow_up"])
    add("G14", "G", "半全场追问", "追问半全场", entity_entry="context", patterns=[r"^半全场$"], priority=89, tags=["follow_up"])
    add("G15", "G", "综合分析追问", "需要综合分析", entity_entry="context", patterns=[r"需要.*综合|综合分析"], priority=88, tags=["follow_up"])
    add("G16", "G", "盘口变化追问", "盘口数字变化", entity_entry="context", complexity="high", patterns=[r"[-+]\d+\.?\d*了$|让分.*了$"], priority=91, tags=["follow_up"])
    add("G17", "G", "多场比赛追问", "批量中追问单场", entity_entry="context", complexity="high", patterns=[r"这场呢|那场呢|土耳其这场|摩洛哥这场"], priority=90, tags=["follow_up"])
    add("G18", "G", "球员情况追问", "追问球员伤停", entity_entry="context", patterns=[r"球员情况|能出战|能不能出场"], priority=87, tags=["follow_up"])
    add("G19", "G", "短确认", "嗯/好/对", entity_entry="context", patterns=[r"^(嗯|好|是的|对|可以|ok|OK)$"], priority=70, tags=["follow_up"])
    add("G20", "G", "格式重写", "指定格式重写", entity_entry="context", patterns=[r"按.*写|主队一段.*客队"], priority=86, tags=["follow_up"])

    # H 前瞻 H01-H08
    add("H01", "H", "争冠悬念", "联赛争冠", entity_entry="league", patterns=[r"争冠.*悬念|还能夺冠"], priority=88)
    add("H02", "H", "降级确定", "降级球队", entity_entry="league", patterns=[r"降级|降班"], priority=86)
    add("H03", "H", "季后赛锁定", "NBA季后赛席位", entity_entry="league", sport="basketball", patterns=[r"锁定.*季后赛|季后赛.*锁定"], priority=90)
    add("H04", "H", "冠军已锁定", "冠军归属已定", entity_entry="league", patterns=[r"锁定冠军|已经冠军|夺冠.*锁定"], priority=88)
    add("H05", "H", "保级形势", "保级分析", entity_entry="league", patterns=[r"保级"], priority=84)
    add("H06", "H", "欧战席位", "欧冠欧联资格", entity_entry="league", patterns=[r"欧战|欧冠资格|欧联资格"], priority=82)
    add("H07", "H", "世界杯进程", "杯赛打到哪一轮", entity_entry="competition", patterns=[r"打到哪|进程|走到哪一步"], priority=80)
    add("H08", "H", "数学出线", "出线形势计算", entity_entry="league", complexity="high", patterns=[r"出线形势|出线.*计算|末轮.*出线"], priority=86)

    # X 边界 X01-X16
    add("X01", "X", "非体育拒答", "政治色情等", entity_entry="none", patterns=[r"政治|色情|暴力|赌博诈骗"], priority=100, tags=["safety"])
    add("X02", "X", "英文提问", "英文自然语言", entity_entry="any", patterns=[r"^[A-Za-z\s,\.?']{10,}$"], priority=60, tags=["language"])
    add("X03", "X", "粤语意图", "粤语表达", entity_entry="any", keywords=["唔该", "点解", "几时", "场波"], priority=60, tags=["language"])
    add("X04", "X", "定位失败", "找不到比赛", entity_entry="match", complexity="high", patterns=[r"找不到|未找到|没有这场"], priority=85, tags=["edge"])
    add("X05", "X", "假阴性风险", "不得断言无赛", entity_entry="team", complexity="high", patterns=[r"没有比赛|均无比赛|无比赛"], priority=99, tags=["regression"])
    add("X06", "X", "中间态外露", "不应输出查询过程", entity_entry="none", complexity="high", patterns=[r"让我查|未找到.*再试|换.*英文名"], priority=98, tags=["output_discipline"])
    add("X07", "X", "内部ID外露", "match_id不应出现", entity_entry="none", complexity="high", patterns=[r"match_id|football_match\.id"], priority=97, tags=["output_discipline"])
    add("X08", "X", "用户辱骂", "辱骂后回到正题", entity_entry="none", patterns=[r"你妈的|他妈|傻逼|瞎.*扯"], priority=55, tags=["edge"])
    add("X09", "X", "冷门赛事", "澳超韩K等", entity_entry="team", patterns=[r"澳超|韩K|沙特联|J联赛"], priority=75)
    add("X10", "X", "无分隔符对阵", "利物浦热刺", entity_entry="match_pair", patterns=[r"^\S+对\S+$|^\S+和\S+这场"], priority=83)
    add("X11", "X", "年份误锚", "错误年份定位", entity_entry="match", complexity="high", patterns=[r"2024-\d{2}-\d{2}.*VS"], priority=96, tags=["regression"])
    add("X12", "X", "主客颠倒", "纠正主客场", entity_entry="match", complexity="high", patterns=[r"主场|客场|挪威.*法国"], priority=94, tags=["regression"])
    add("X13", "X", "数据诚实", "缺失字段声明", entity_entry="match", patterns=[r"数据暂缺|数据不足"], priority=70)
    add("X14", "X", "矛盾推荐", "避免双向推荐", entity_entry="match", complexity="high", patterns=[r"主不败.*客不败"], priority=88, tags=["guardrail"])
    add("X15", "X", "盈利承诺", "不得承诺盈利", entity_entry="none", patterns=[r"保证.*赢|100%.*命中"], priority=92, tags=["guardrail"])
    add("X16", "X", "网络兜底", "搜索后重新定位", entity_entry="match", patterns=[r"搜索.*确认|网上.*查"], priority=72)

    assert len(types) == 120, f"expected 120 types, got {len(types)}"
    return types


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc = {"version": "1.0", "description": "Foretell complex question taxonomy (120 types)", "types": _types()}
    with OUT.open("w", encoding="utf-8") as f:
        yaml.dump(doc, f, allow_unicode=True, sort_keys=False, default_flow_style=False, width=120)
    print(f"Wrote {len(doc['types'])} types to {OUT}")


if __name__ == "__main__":
    main()
