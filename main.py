"""Foretell 智能体命令行入口。"""

import argparse
import sys
import uuid

from config.settings import get_settings
from foretell import create_foretell_agent


def _default_thread_id(user_id: str) -> str:
    return f"{user_id}:{uuid.uuid4().hex[:8]}"


def run_once(agent, question: str, user_id: str, thread_id: str) -> str:
    config = {"configurable": {"user_id": user_id, "thread_id": thread_id}}
    result = agent.invoke(
        {"messages": [{"role": "user", "content": question}]},
        config=config,
    )
    return result["messages"][-1].content


def run_interactive(agent, user_id: str, thread_id: str) -> None:
    config = {"configurable": {"user_id": user_id, "thread_id": thread_id}}
    print("Foretell 已就绪。输入问题开始对话，输入 exit 或 quit 退出。\n")

    while True:
        try:
            question = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            break

        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("再见。")
            break

        result = agent.invoke(
            {"messages": [{"role": "user", "content": question}]},
            config=config,
        )
        print(f"\nForetell: {result['messages'][-1].content}\n")


def main() -> None:
    settings = get_settings()
    parser = argparse.ArgumentParser(description="Foretell — 体育赛事智能助手")
    parser.add_argument("question", nargs="?", help="单次提问（省略则进入交互模式）")
    parser.add_argument(
        "--user-id",
        default="cli-user",
        help="用户 ID，用于会话隔离",
    )
    parser.add_argument(
        "--thread-id",
        default=None,
        help="会话线程 ID；省略则自动生成 {user_id}:{uuid}",
    )
    args = parser.parse_args()

    user_id = args.user_id
    thread_id = args.thread_id or _default_thread_id(user_id)
    agent = create_foretell_agent(deploy_env=settings.deploy_env)

    if args.question:
        print(run_once(agent, args.question, user_id, thread_id))
    else:
        if not sys.stdin.isatty():
            question = sys.stdin.read().strip()
            if question:
                print(run_once(agent, question, user_id, thread_id))
                return
        run_interactive(agent, user_id, thread_id)


if __name__ == "__main__":
    main()
