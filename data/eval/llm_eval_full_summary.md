# Foretell LLM Eval Full Summary (120 types)

- **Evaluated at**: 2026-06-30
- **Total types**: 120/120
- **Pass**: 37 | **Fail**: 83
- **Partial tools sufficient**: 69

## Distribution by Scenario

| Scenario | Pass | Fail | Pass rate |
|----------|------|------|-----------|
| A | 12 | 6 | 67% |
| B | 6 | 10 | 38% |
| C | 2 | 6 | 25% |
| D | 3 | 7 | 30% |
| E | 4 | 10 | 29% |
| F | 3 | 7 | 30% |
| G | 1 | 19 | 5% |
| H | 2 | 6 | 25% |
| X | 4 | 12 | 25% |

## Top 10 Gap Types

- **none**: 25
- **implementation_gap**: 17
- **routing_gap**: 16
- **data_gap**: 14
- **data_missing_gap**: 5
- **None**: 4
- **context_gap**: 2

## P0 Regression (Phase 1)

- A08: PASS (score 4.15)
- A17: PASS (score 4.15)
- X05: FAIL (score 2.89)
- X06: PASS (score 4.26)
- X12: FAIL (score 3.12)
- B01: FAIL (score 3.02)
- B09: FAIL (score 2.99)
- E05: PASS (score 4.11)
- G01: FAIL (score 2.99)
- G07: FAIL (score 2.94)

## Artifacts

```
data/eval/answer_playbooks_full_120.yaml
data/eval/route_matrix_final.yaml
data/eval/path_attempts/{120}.yaml
data/eval/atomic_decompositions/{120}.yaml
```
