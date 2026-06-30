"""汇总 path_attempts_v3/*.yaml 的 v3 verdict,生成对比表数据。"""
import sys
from pathlib import Path
import yaml

V3 = Path(__file__).resolve().parent.parent / "data" / "eval" / "path_attempts_v3"

rows = []
for f in sorted(V3.glob("*.yaml")):
    try:
        d = yaml.safe_load(f.read_text(encoding="utf-8"))
    except Exception as e:
        rows.append((f.stem, "?", f"PARSE_ERR {e}", ""))
        continue
    tid = d.get("type_id", f.stem)
    v2 = (d.get("v2_verdict") or "").replace("\n", " ")[:50]
    v3 = d.get("v3_verdict") or d.get("verdict_tier") or "?"
    tier = d.get("verdict_tier") or ""
    summary = (d.get("change_summary") or "").replace("\n", " ")[:80]
    rows.append((tid, tier, v2, summary))

# 按批分组
batches = {
    "A+X": ["A18", "X15", "X16"],
    "B+C": ["B02", "B04", "B06", "B08", "B09", "B10", "C02", "C07"],
    "D+E": ["D01", "D05", "D06", "D09", "D10", "E05", "E06", "E07"],
    "F+G": ["F03", "G03", "G05", "G07", "G08"],
    "H": ["H05"],
}

by_id = {r[0]: r for r in rows}
from collections import Counter
cnt = Counter()
print("=== v3 verdict 汇总 ===")
for batch, ids in batches.items():
    print(f"\n## {batch}")
    for tid in ids:
        if tid in by_id:
            r = by_id[tid]
            tier = r[1]
            cnt[tier] += 1
            print(f"  {tid} | {tier} | v2:{r[2][:40]} | {r[3][:60]}")

print(f"\n=== 统计 ===")
print(f"总型数: {sum(cnt.values())}")
for k, v in sorted(cnt.items()):
    print(f"  {k}: {v}")
