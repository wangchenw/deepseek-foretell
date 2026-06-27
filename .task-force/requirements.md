# Foretell 复杂提问测试数据集 — 需求摘要

## 目标

从生产 MySQL `ai.foretell_sessions`（约 14.4 万会话）抽取用户提问，构建 **120+ 复杂题型** 评测集，覆盖场景 A–H、四种实体入口、多轮追问链。

## 数据源

- 表：`ai.foretell_sessions`
- 多轮模型：`runs[i].input.input_content` 每 run 一轮用户提问
- 环境变量：`FORETELL_SESSION_DB_URL`

## 交付物

| 文件 | 说明 |
|------|------|
| `data/eval/taxonomy.yaml` | 120 个 type_id 及匹配规则 |
| `data/eval/raw_questions.jsonl` | 抽取中间数据 |
| `data/eval/foretell_complex_questions.jsonl` | 最终评测集 |
| `data/eval/coverage_report.json` | 覆盖率报告 |
| `scripts/extract_session_questions.py` | 抽取脚本 |
| `scripts/classify_questions.py` | 分类脚本 |
| `scripts/build_eval_dataset.py` | 构建脚本 |

## 验收标准

1. taxonomy ≥120 types
2. JSONL ≥120 行，每 type 至少 1 条
3. multi_turn ≥20 条
4. 含 feedback #001–#003 回归用例
5. missing_types 为空

## 流水线

```bash
uv run python scripts/extract_session_questions.py
uv run python scripts/classify_questions.py
uv run python scripts/build_eval_dataset.py
```
