from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="用户消息")
    thread_id: str | None = Field(
        default=None,
        description="会话线程 ID；省略时自动生成 {user_id}:{uuid}",
    )
    stream: bool = Field(default=False, description="是否流式返回（Phase 4 实现）")


class ChatResponse(BaseModel):
    thread_id: str
    content: str
