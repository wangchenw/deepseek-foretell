from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse

from api.auth import get_user_id
from api.schemas import ChatRequest, ChatResponse
from api.streaming import stream_agent_messages
from api.threads import assert_thread_owned_by_user, default_thread_id
from config.settings import get_settings
from foretell import create_foretell_agent

app = FastAPI(title="Foretell API", version="0.1.0")


@lru_cache
def _get_agent_for_date(current_date: str):
    settings = get_settings()
    return create_foretell_agent(deploy_env=settings.deploy_env)


def get_agent():
    current_date = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    return _get_agent_for_date(current_date)


get_agent.cache_clear = _get_agent_for_date.cache_clear


def _resolve_thread_id(body: ChatRequest, user_id: str) -> str:
    thread_id = body.thread_id or default_thread_id(user_id)
    if body.thread_id:
        try:
            assert_thread_owned_by_user(thread_id, user_id)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc
    return thread_id


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/v1/chat", response_model=None)
def chat(
    body: ChatRequest,
    user_id: str = Depends(get_user_id),
) -> ChatResponse | StreamingResponse:
    thread_id = _resolve_thread_id(body, user_id)
    config = {"configurable": {"user_id": user_id, "thread_id": thread_id}}
    input_state = {"messages": [{"role": "user", "content": body.message}]}
    agent = get_agent()

    if body.stream:
        return StreamingResponse(
            stream_agent_messages(agent, input_state, config, thread_id),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    result = agent.invoke(input_state, config=config)
    content = result["messages"][-1].content

    return ChatResponse(thread_id=thread_id, content=content)
