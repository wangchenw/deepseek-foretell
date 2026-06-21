from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, status

from api.auth import get_user_id
from api.schemas import ChatRequest, ChatResponse
from api.threads import assert_thread_owned_by_user, default_thread_id
from config.settings import get_settings
from foretell import create_foretell_agent

app = FastAPI(title="Foretell API", version="0.1.0")


@lru_cache
def get_agent():
    settings = get_settings()
    return create_foretell_agent(deploy_env=settings.deploy_env)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/chat", response_model=ChatResponse)
def chat(
    body: ChatRequest,
    user_id: str = Depends(get_user_id),
):
    if body.stream:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="流式响应将在 Phase 4 实现",
        )

    thread_id = body.thread_id or default_thread_id(user_id)
    if body.thread_id:
        try:
            assert_thread_owned_by_user(thread_id, user_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc
    config = {"configurable": {"user_id": user_id, "thread_id": thread_id}}

    agent = get_agent()
    result = agent.invoke(
        {"messages": [{"role": "user", "content": body.message}]},
        config=config,
    )
    content = result["messages"][-1].content

    return ChatResponse(thread_id=thread_id, content=content)
