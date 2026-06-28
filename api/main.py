import time
from datetime import datetime
from functools import lru_cache
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import StreamingResponse

from api.auth import get_user_id
from api.schemas import ChatRequest, ChatResponse
from api.streaming import _extract_text_content, stream_agent_messages
from api.threads import assert_thread_owned_by_user, default_thread_id
from config.settings import get_settings
from foretell import create_foretell_agent
from foretell.conversation_log import log_conversation_turn

app = FastAPI(title="Foretell API", version="0.1.0")


# 「同一天内大家共用同一个 Agent；到了新的一天，缓存 miss，重建一个带新日期的 Agent。」
@lru_cache
def _get_agent_for_date(current_date: str):
    settings = get_settings()
    return create_foretell_agent(deploy_env=settings.deploy_env)


def get_agent():
    current_date = datetime.now(ZoneInfo("Asia/Shanghai")).date().isoformat()
    return _get_agent_for_date(current_date)


setattr(get_agent, "cache_clear", _get_agent_for_date.cache_clear)


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
            stream_agent_messages(
                agent,
                input_state,
                config,
                thread_id,
                user_id,
                body.message,
            ),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    started = time.monotonic()
    try:
        result = agent.invoke(input_state, config=config)
    except Exception as exc:
        log_conversation_turn(
            user_id=user_id,
            thread_id=thread_id,
            user_message=body.message,
            assistant_message=None,
            stream=False,
            status="error",
            error_message=str(exc),
            latency_ms=int((time.monotonic() - started) * 1000),
        )
        raise

    content = _extract_text_content(result["messages"][-1].content)

    status_value = "ok" if content.strip() else "empty_reply"
    log_conversation_turn(
        user_id=user_id,
        thread_id=thread_id,
        user_message=body.message,
        assistant_message=content,
        stream=False,
        status=status_value,
        latency_ms=int((time.monotonic() - started) * 1000),
    )

    return ChatResponse(thread_id=thread_id, content=content)
