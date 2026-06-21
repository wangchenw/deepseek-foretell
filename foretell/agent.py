from deepagents import create_deep_agent

from config.llm import get_chat_model
from config.settings import FORETELL_SKILLS_DIR
from foretell.backends import (
    create_agent_backend,
    create_checkpointer,
    create_store,
)
from foretell.prompts import SYSTEM_PROMPT
from foretell.tools import get_tools


def create_foretell_agent(deploy_env: str = "dev"):
    """创建 Foretell 体育赛事智能助手。

    内置能力（Deep Agents Harness 自动提供）：
    - 任务规划（write_todos）
    - 文件系统（ls / read_file / write_file / edit_file / glob / grep）
    - 子 Agent 委派（task）
    - 按需加载技能（foretell/skills/）

    调用时在 config 中传入 user_id 与 thread_id，例如::

        config = {
            "configurable": {
                "user_id": "user-123",
                "thread_id": "user-123:session-abc",
            }
        }
        agent.invoke({"messages": [...]}, config=config)
    """
    return create_deep_agent(
        name="foretell",
        model=get_chat_model(),
        tools=get_tools(),
        system_prompt=SYSTEM_PROMPT,
        backend=create_agent_backend,
        skills=[str(FORETELL_SKILLS_DIR)],
        checkpointer=create_checkpointer(deploy_env),
        store=create_store(deploy_env),
    )
