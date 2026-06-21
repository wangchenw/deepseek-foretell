from fastapi import Header, HTTPException, status

from config.settings import get_settings


def get_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    authorization: str | None = Header(default=None),
) -> str:
    """解析请求中的 user_id。dev 环境使用 X-User-Id；prod 仅接受 JWT（Phase 4 实现）。"""
    settings = get_settings()

    if settings.is_dev:
        if not x_user_id or not x_user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="开发环境需在请求头中提供 X-User-Id",
            )
        return x_user_id.strip()

    if authorization and authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="生产 JWT 鉴权尚未实现",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="生产环境需提供有效 JWT，不可使用 X-User-Id",
    )
