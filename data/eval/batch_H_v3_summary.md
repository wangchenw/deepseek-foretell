# v3 eval 批次汇总 — H

- 验证日期: 2026-06-30
- 范围: H 语义精度(v2 ⚠️ 子集)

| type_id | 名称 | v2 | v3 | 变化 |
|---------|------|-----|-----|------|
| H05 | 保级形势 | ⚠️ | ✅ | ↑ promotion_id+promotion_name 填充 + season 空壳过滤(played=38 非 0) |

**批次结论**: 1/1 升档 ✅。standings 三处修复全部生效:season 空壳过滤(pt.total>0)、promotion_id 暴露、promotion_name 填充(JOIN football_promotions.name_zh)。v2 撞墙(promotion_id 已编码但工具未暴露 + 休赛期空壳)全部解决。
