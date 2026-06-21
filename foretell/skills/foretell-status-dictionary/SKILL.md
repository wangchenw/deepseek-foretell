---
name: foretell-status-dictionary
description: Tool 层状态码到用户可见标注的映射。当解读工具返回结果、决定如何向用户呈现数据缺失或异常时使用。
---

# 状态码字典

Tool 层返回统一 envelope，`code` 字段由**工具判定**，LLM **不得猜测**状态。

## 状态码表（见设计 Spec §8.3）

| code | 用户可见标注 | 行为 |
|------|-------------|------|
| `OK` | （正常分析） | 全权重使用数据 |
| `DATA_MISSING` | 数据不足 | 跳过该细项，不编造 |
| `NOT_APPLICABLE` | 不适用 + 原因 | 提供替代信息或说明原因 |
| `SKIP_MATCH` | 盘口数据不足，建议跳过此场 | 欧赔+亚盘均缺时使用 |
| `ENTITY_NOT_FOUND` | 未找到比赛/实体 | 可触发网络搜索兜底（最多 1 次） |
| `PARTIAL` | 按维度分别标注 | 降权使用，标注缺失维度 |

## 使用规则

1. 读取 envelope 中的 `code`，按上表决定输出策略
2. `DATA_MISSING` / `PARTIAL`：诚实说明缺口，不填充假数据
3. `ENTITY_NOT_FOUND`：告知未找到，可建议用户核对队名或日期
4. `NOT_APPLICABLE`：说明不适用原因（如指定 G7 不存在）
5. `SKIP_MATCH`：建议用户跳过该场，不强行分析

## 禁止行为

- 忽略 `code` 直接编造比分、赔率或赛果
- 将 `ENTITY_NOT_FOUND` 当作「数据不足」模糊带过
- 向用户暴露 envelope JSON 或内部字段名
