"""One-off helper: redact secrets from 配置.md during git history rewrite."""

import re
from pathlib import Path

path = Path("配置.md")
if not path.exists():
    raise SystemExit(0)

text = path.read_text(encoding="utf-8")
text = re.sub(r"lsv2_pt_[A-Za-z0-9_]+", "<YOUR_LANGSMITH_API_KEY>", text)
text = re.sub(r"sk-cp-[A-Za-z0-9_-]+", "<YOUR_MINIMAX_API_KEY>", text)
path.write_text(text, encoding="utf-8")
