# Foretell LLM Eval Full Summary (120 types)

- **Evaluated at**: 2026-06-28
- **Total types**: 120/120
- **Pass**: 75 | **Fail**: 45
- **Partial tools sufficient**: 36

## Distribution by Scenario

| Scenario | Pass | Fail | Pass rate |
|----------|------|------|-----------|
| A | 17 | 1 | 94% |
| B | 12 | 4 | 75% |
| C | 6 | 2 | 75% |
| D | 10 | 0 | 100% |
| E | 13 | 1 | 93% |
| F | 9 | 1 | 90% |
| G | 0 | 20 | 0% |
| H | 5 | 3 | 62% |
| X | 3 | 13 | 19% |

## Top 10 Gap Types

- **data_missing_gap**: 18
- **routing_gap**: 15
- **data_gap**: 9
- **implementation_gap**: 3

## P0 Regression (Phase 1)

- A08: PASS (score 4.15)
- A17: PASS (score 4.15)
- X05: PASS (score 4.16)
- X06: PASS (score 4.26)
- X12: PASS (score 4.26)
- B01: FAIL (score 2.65)
- B09: FAIL (score 2.65)
- E05: FAIL (score 2.99)
- G01: FAIL (score 2.82)
- G07: FAIL (score 2.97)

## Artifacts

```
data/eval/answer_playbooks_full_120.yaml
data/eval/route_matrix_final.yaml
data/eval/path_attempts/{120}.yaml
data/eval/atomic_decompositions/{120}.yaml
```
