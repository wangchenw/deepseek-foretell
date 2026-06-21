from fastapi import Header, HTTPException, status

from config.settings import get_settings


def get_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    authorization: str | None = Header(default=None),
) -> str:
    """解析请求中的 user_id。dev 环境使用 X-User-Id；prod 预留 JWT 解析入口。"""
    settings = get_settings()

    if settings.is_dev:
        if not x_user_id or not x_user_id.strip():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="开发环境需在请求头中提供 X-User-Id",
            )
        return x_user_id.strip()

    if x_user_id and x_user_id.strip():
        return x_user_id.strip()

    if authorization and authorization.startswith("Bearer "):
        # Phase 4：接入 JWT 校验；当前为 stub，拒绝未实现路径
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="生产 JWT 鉴权尚未实现，请使用 X-User-Id（仅开发）",
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="未提供有效鉴权信息",
    )
