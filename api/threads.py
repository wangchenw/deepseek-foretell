import uuid


def default_thread_id(user_id: str) -> str:
    return f"{user_id}:{uuid.uuid4().hex[:8]}"


def assert_thread_owned_by_user(thread_id: str, user_id: str) -> None:
    prefix = f"{user_id}:"
    if not thread_id.startswith(prefix):
        raise ValueError(f"thread_id 必须属于当前用户（前缀 {prefix!r}）")
