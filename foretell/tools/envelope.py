"""统一 Tool 响应 envelope 构造。"""

import json
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from foretell.tools.status_codes import StatusCode


def _json_default(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, date):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def make_envelope(
    code: StatusCode | str,
    dimension: str,
    data: Any = None,
    match_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> str:
    """构造标准 envelope 并返回 JSON 字符串。

    Args:
        code: 状态码（StatusCode 或字符串）。
        dimension: 数据维度标识，如 match_entity、schedule_by_date。
        data: 业务数据载荷，默认为空 dict。
        match_id: 关联比赛 ID（可选）。
        meta: 元信息，如 source、freshness（可选）。
    """
    envelope: dict[str, Any] = {
        "code": code.value if isinstance(code, StatusCode) else str(code),
        "dimension": dimension,
        "data": data if data is not None else {},
    }
    if match_id is not None:
        envelope["match_id"] = match_id
    if meta is not None:
        envelope["meta"] = meta
    return json.dumps(envelope, ensure_ascii=False, default=_json_default)
