"""Download nami openapi docs and status codes to data/eval/nami_docs/."""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from pathlib import Path

OUT_DIR = Path("data/eval/nami_docs")
HEADERS_BASE = {
    "Accept": "*/*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Referer": "https://www.nami.com/en/docs?id=2002",
}

# Foretell 主要用足球/篮球；完整 doc_id 列表见 _discovered_doc_ids.json
DOC_IDS = [2002, 2003]


def _token() -> str:
    token = os.environ.get("NAMI_DOC_TOKEN", "")
    if not token:
        raise SystemExit("Set NAMI_DOC_TOKEN (nami.com cookie token=...) before running.")
    return token


def get_json(url: str) -> dict:
    headers = {**HEADERS_BASE, "Cookie": f"token={_token()}; locale=en"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def save(name: str, data: object) -> Path:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUT_DIR / name
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {path} ({path.stat().st_size:,} bytes)")
    return path


def slug(title: str, doc_id: int) -> str:
    safe = re.sub(r"[^\w\u4e00-\u9fff-]+", "_", title).strip("_")[:50]
    return f"openapi_{doc_id}_{safe}"


def extract_status_section(spec: dict) -> dict | list | None:
    for child in spec.get("main_page", {}).get("data", {}).get("children", []):
        if child.get("title") == "状态码":
            return child.get("data")
    return None


def blocks_to_markdown(data: object) -> str:
    if isinstance(data, str):
        return data
    if isinstance(data, dict):
        if data.get("type") == "text":
            return str(data.get("data", ""))
        if "blocks" in data:
            return "\n\n".join(blocks_to_markdown(b) for b in data["blocks"])
    if isinstance(data, list):
        return "\n\n".join(blocks_to_markdown(x) for x in data)
    return str(data)


def fetch_doc(doc_id: int) -> dict | None:
    time.sleep(0.6)
    resp = get_json(f"https://www.nami.com/api/v2/doc/get?id={doc_id}")
    if resp.get("code") != 0:
        print(f"doc {doc_id}: {resp.get('msg')}")
        return None
    return resp.get("data")


def main() -> None:
    index: list[dict] = []
    catalog: list[dict] = []
    status_sections: dict[str, object] = {}

    for doc_id in DOC_IDS:
        spec = fetch_doc(doc_id)
        if not spec:
            continue
        info = spec.get("info") or {}
        title = info.get("title") or f"doc_{doc_id}"
        fname = slug(title, doc_id) + ".json"
        save(fname, spec)
        index.append(
            {
                "doc_id": doc_id,
                "title": title,
                "version": info.get("version"),
                "description": info.get("description"),
                "server": (spec.get("servers") or [{}])[0].get("url"),
                "tags": [t.get("name") for t in (spec.get("tags") or [])],
                "path_count": len(spec.get("paths") or {}),
                "file": fname,
                "status_codes_file": f"status_codes_{doc_id}.md",
            }
        )
        for path, methods in (spec.get("paths") or {}).items():
            for method, detail in methods.items():
                if not isinstance(detail, dict):
                    continue
                catalog.append(
                    {
                        "doc_id": doc_id,
                        "api_title": title,
                        "method": method.upper(),
                        "path": path,
                        "summary": detail.get("summary"),
                        "tag": (detail.get("tags") or [None])[0],
                    }
                )
        section = extract_status_section(spec)
        if section:
            status_sections[str(doc_id)] = section
            md_path = OUT_DIR / f"status_codes_{doc_id}.md"
            md_path.write_text(blocks_to_markdown(section), encoding="utf-8")
            print(f"saved {md_path} ({md_path.stat().st_size:,} bytes)")

    save("_index.json", index)
    save("_api_catalog.json", catalog)
    save("_status_code_sections.json", status_sections)
    print("done")


if __name__ == "__main__":
    main()
