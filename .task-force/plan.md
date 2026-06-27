# Implementation Plan: Foretell 复杂提问测试数据集

## Overview

从 MySQL `ai.foretell_sessions` 抽取 145,109 条会话，经 taxonomy 分类与代表样本选取，构建 120 题型评测集。

## 交付物

| 文件 | 状态 |
|------|------|
| `data/eval/taxonomy.yaml` | 120 types |
| `data/eval/raw_questions.jsonl` | 145,109 sessions |
| `data/eval/foretell_complex_questions.jsonl` | 120 cases |
| `data/eval/coverage_report.json` | missing_types=[] |
| `data/eval/spot_check_report.json` | 30 条抽检 |
| `tests/eval/test_cases.yaml` | 10 P0 用例 |

## 流水线

```bash
export FORETELL_SESSION_DB_URL=mysql+pymysql://...
uv run python scripts/extract_session_questions.py
uv run python scripts/classify_questions.py
uv run python scripts/build_eval_dataset.py
uv run python scripts/spot_check_dataset.py
uv run python scripts/export_p0_test_cases.py
```

## 验收结果

- 120/120 types 覆盖
- 104 条多轮对话（>=20 要求）
- 101 条生产样本 + 19 条合成
- feedback #001–#003 回归用例已纳入
