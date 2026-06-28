#!/usr/bin/env python3
"""Phase 2a-alt: eval-only checkpointer demo for G multi-turn (no foretell/ changes)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from llm_eval_common import EVAL_DIR, P0_TYPE_IDS, dump_yaml, load_yaml, today_iso  # noqa: E402

DEMO_PATH = EVAL_DIR / "phase2a_checkpointer_demo.yaml"


class TurnCheckpointer:
    """Demonstration-level turn state for eval; not wired to production agent."""

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def save(self, session_id: str, turn: int, state: dict[str, Any]) -> None:
        self._sessions.setdefault(session_id, {})[turn] = dict(state)

    def load(self, session_id: str, turn: int | None = None) -> dict[str, Any] | None:
        turns = self._sessions.get(session_id, {})
        if turn is not None:
            return turns.get(turn)
        if not turns:
            return None
        return turns[max(turns.keys())]

    def fork_context(self, session_id: str, from_turn: int) -> dict[str, Any]:
        state = self.load(session_id, from_turn) or {}
        return {
            "match_id": state.get("match_id"),
            "analysis_done": state.get("analysis_done", False),
            "follow_up_only": True,
        }


def simulate_g01(checkpointer: TurnCheckpointer) -> dict[str, Any]:
    sid = "G01-demo"
    checkpointer.save(
        sid,
        1,
        {
            "match_id": None,
            "lottery_code": "004",
            "analysis_done": True,
            "segments": 6,
        },
    )
    ctx = checkpointer.fork_context(sid, 1)
    turn2_needs = ["maintain_context", "synthesize_answer"]
    would_pass = ctx.get("analysis_done") and ctx.get("follow_up_only")
    return {
        "type_id": "G01",
        "turn1_state": checkpointer.load(sid, 1),
        "turn2_context": ctx,
        "required_atomics_turn2": turn2_needs,
        "simulated_pass": would_pass,
        "production_gap": "agent checkpointer 未接入；eval 仅证明 turn2 不应 re-resolve",
    }


def simulate_g07(checkpointer: TurnCheckpointer) -> dict[str, Any]:
    sid = "G07-demo"
    checkpointer.save(
        sid,
        1,
        {
            "criteria": ["赔率<=1.5", "近5场>=2球", "伤停", "媒体热度", "跨窗口"],
            "lottery_play": "301",
        },
    )
    ctx = checkpointer.fork_context(sid, 1)
    return {
        "type_id": "G07",
        "turn1_state": checkpointer.load(sid, 1),
        "turn2_context": ctx,
        "simulated_pass": bool(ctx.get("criteria")),
        "production_gap": "跨窗口引用需 thread_id + checkpointer；stub 工具限制深度筛选",
    }


def main() -> None:
    cp = TurnCheckpointer()
    report = {
        "demo_at": today_iso(),
        "scope": "eval-only prototype in scripts/eval_checkpointer_demo.py",
        "does_not_modify": ["foretell/tools", "foretell/skills"],
        "simulations": [simulate_g01(cp), simulate_g07(cp)],
        "conclusion": (
            "checkpointer 逻辑可模拟；G01/G07 生产失败主因仍是 lottery/stub，"
            "context 层需 Phase3 接入 LangGraph checkpointer"
        ),
        "phase2b_action": "继续全量评估，G 类标 pipeline_gap",
    }
    dump_yaml(DEMO_PATH, report)
    print(f"Checkpointer demo -> {DEMO_PATH}")


if __name__ == "__main__":
    main()
