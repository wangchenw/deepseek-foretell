from fastapi import Header, HTTPException, status

from config.settings import get_settings

# get_user_id 是 FastAPI 的依赖注入函数，用来从请求头里解析当前用户是谁，并作为 user_id 传给需要鉴权的路由。

def get_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
    authorization: str | None = Header(default=None),  # 保留参数，便于以后接 JWT
) -> str:
    """解析请求中的 user_id。当前 dev/prod 均使用 X-User-Id。"""
    if not x_user_id or not x_user_id.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="需在请求头中提供 X-User-Id",
        )
    return x_user_id.strip()