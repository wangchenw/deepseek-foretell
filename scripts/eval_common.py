"""Shared utilities for Foretell eval dataset pipeline."""

from __future__ import annotations

import hashlib
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

import pymysql
import yaml
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TAXONOMY_PATH = PROJECT_ROOT / "data" / "eval" / "taxonomy.yaml"
EVAL_DIR = PROJECT_ROOT / "data" / "eval"

load_dotenv(PROJECT_ROOT / ".env")

MAX_RUN_EXTRACT = 16

LOTTERY_TEMPLATE_RE = re.compile(
    r"分析【\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+竞彩足球周[一二三四五六日]\d{3}\s+.+?】",
    re.IGNORECASE,
)
LOTTERY_TEMPLATE_NORM = "分析【{DATE} 竞彩足球{WEEKDAY}{CODE} {COMP} {HOME} VS {AWAY}】的赛事的胜平负、比分结果"


@dataclass(frozen=True)
class TaxonomyType:
    id: str
    scenario: str
    name: str
    description: str
    entity_entry: str
    sport: str
    complexity: str
    patterns: list[str]
    keywords: list[str]
    priority: int
    tags: list[str]


def parse_session_db_url(url: str) -> dict[str, Any]:
    """Parse mysql+pymysql://user:pass@host:port/db?charset=utf8mb4."""
    if url.startswith("mysql+pymysql://"):
        url = "mysql://" + url[len("mysql+pymysql://") :]
    elif url.startswith("mysql://"):
        pass
    else:
        raise ValueError(f"Unsupported DB URL scheme: {url[:30]}")

    parsed = urlparse(url)
    database = parsed.path.lstrip("/") or None
    if database and "?" in database:
        database = database.split("?", 1)[0]
    return {
        "host": parsed.hostname,
        "port": parsed.port or 3306,
        "user": unquote(parsed.username or ""),
        "password": unquote(parsed.password or ""),
        "database": database or "ai",
        "charset": "utf8mb4",
        "connect_timeout": 15,
        "read_timeout": 120,
        "write_timeout": 120,
    }


def get_session_connection() -> pymysql.connections.Connection:
    url = os.environ.get("FORETELL_SESSION_DB_URL")
    if not url:
        raise RuntimeError("FORETELL_SESSION_DB_URL is not set in environment")
    kwargs = parse_session_db_url(url)
    return pymysql.connect(**kwargs)


def load_taxonomy(path: Path | None = None) -> list[TaxonomyType]:
    path = path or TAXONOMY_PATH
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    types: list[TaxonomyType] = []
    for item in data["types"]:
        types.append(
            TaxonomyType(
                id=item["id"],
                scenario=item["scenario"],
                name=item["name"],
                description=item.get("description", ""),
                entity_entry=item.get("entity_entry", "unknown"),
                sport=item.get("sport", "any"),
                complexity=item.get("complexity", "medium"),
                patterns=item.get("patterns", []),
                keywords=item.get("keywords", []),
                priority=int(item.get("priority", 50)),
                tags=item.get("tags", []),
            )
        )
    types.sort(key=lambda t: t.priority, reverse=True)
    return types


def normalize_question(text: str) -> tuple[str, str]:
    """Return (normalized_text, pattern_hash)."""
    q = text.strip()
    if LOTTERY_TEMPLATE_RE.search(q):
        norm = LOTTERY_TEMPLATE_NORM
        if "并描写" in q or "分析内容" in q:
            norm += "，并描写100-300字的分析内容"
        return norm, hashlib.md5(norm.encode()).hexdigest()[:12]

    norm = q
    norm = re.sub(r"\d{4}-\d{2}-\d{2}(\s+\d{2}:\d{2}:\d{2})?", "{DATE}", norm)
    norm = re.sub(r"周[一二三四五六日]\d{3}", "{WEEKDAY}{CODE}", norm)
    norm = re.sub(r"\s+", " ", norm).strip()
    return norm, hashlib.md5(norm.encode()).hexdigest()[:12]


def _matches_type(text: str, t: TaxonomyType) -> bool:
    for pat in t.patterns:
        if re.search(pat, text, re.IGNORECASE):
            return True
    if t.keywords and not t.patterns:
        ql = text.lower()
        return any(kw.lower() in ql for kw in t.keywords)
    return False


def classify_text(text: str, taxonomy: list[TaxonomyType] | None = None) -> TaxonomyType | None:
    if not text or not text.strip():
        return None
    taxonomy = taxonomy or load_taxonomy()
    q = text.strip()
    for t in taxonomy:
        if _matches_type(q, t):
            return t
    return None


def classify_session_turns(turns: list[str], taxonomy: list[TaxonomyType] | None = None) -> dict[str, Any]:
    """Classify a session; primary from first turn, follow-ups from later turns."""
    taxonomy = taxonomy or load_taxonomy()
    turn_types: list[str | None] = []
    for turn in turns:
        matched = classify_text(turn, taxonomy)
        turn_types.append(matched.id if matched else None)

    primary = classify_text(turns[0], taxonomy) if turns else None
    follow_types = [tid for tid in turn_types[1:] if tid]

    return {
        "primary_type_id": primary.id if primary else None,
        "primary_scenario": primary.scenario if primary else None,
        "turn_type_ids": turn_types,
        "follow_type_ids": follow_types,
    }


def complexity_score(
    turns: list[str],
    type_id: str | None,
    taxonomy: list[TaxonomyType] | None = None,
) -> int:
    score = 0
    if len(turns) >= 2:
        score += 2
    if len(turns) >= 4:
        score += 1
    if turns and len(turns[0]) > 60:
        score += 1
    if turns and re.search(r"【.*VS.*】", turns[0], re.I):
        score += 1
    if type_id and type_id.startswith("E"):
        score += 2
    if type_id and type_id.startswith("G"):
        score += 1
    if type_id and type_id.startswith("X"):
        score += 1
    if any(re.search(r"歧义|女足|U21|俱乐部|纠正", t) for t in turns):
        score += 1
    if any(re.search(r"同样逻辑|刚才|继续|再分析|重新", t) for t in turns[1:]):
        score += 2
    return score


def user_id_prefix(session_id: str) -> str:
    if "_" in session_id:
        return session_id.split("_", 1)[0]
    return session_id


def ensure_eval_dir() -> Path:
    EVAL_DIR.mkdir(parents=True, exist_ok=True)
    return EVAL_DIR
