#!/usr/bin/env python3
"""Foretell Eval V2 orchestrator: Phase 1 check -> decision -> 2a -> 2b."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
EVAL_DIR = ROOT / "data" / "eval"


def _run(cmd: list[str], label: str) -> int:
    print(f"\n{'='*60}\n[{label}]\n{' '.join(cmd)}\n{'='*60}")
    proc = subprocess.run(cmd, cwd=ROOT)
    if proc.returncode != 0:
        print(f"WARN: {label} exited {proc.returncode}", file=sys.stderr)
    return proc.returncode


def _phase1_report() -> None:
    summary = EVAL_DIR / "llm_eval_summary.md"
    playbooks = EVAL_DIR / "answer_playbooks.yaml"
    if not summary.exists() or not playbooks.exists():
        print("Phase 1 artifacts missing; run run_llm_eval_phase1.py first", file=sys.stderr)
        sys.exit(1)
    print("\n# Phase 1 Final Report (cached)")
    print(summary.read_text(encoding="utf-8")[:2000])


def main() -> None:
    started = datetime.now(timezone.utc).isoformat()
    print(f"Foretell Eval V2 START {started}")

    _phase1_report()

    _run([sys.executable, str(SCRIPTS / "llm_eval_decision.py")], "Decision tree")
    decision_path = EVAL_DIR / "phase2_decision.json"
    decision = json.loads(decision_path.read_text(encoding="utf-8"))
    route = decision.get("selected_route", "Phase_2a_priority_order")
    print(f"\nAuto route: {route}\nReason: {decision.get('reason')}")

    if route in {"Phase_2a_lottery", "Phase_2a_priority_order"}:
        _run([sys.executable, str(SCRIPTS / "phase2a_lottery_diagnose.py")], "Phase 2a lottery diagnose")

    if route in {"Phase_2a_checkpointer", "Phase_2a_priority_order"}:
        _run([sys.executable, str(SCRIPTS / "eval_checkpointer_demo.py")], "Phase 2a checkpointer demo")

    _run(
        [sys.executable, str(SCRIPTS / "generate_atomic_decompositions_batch.py"), "--all"],
        "Generate atomic decompositions (110 templates)",
    )

    _run(
        [
            sys.executable,
            str(SCRIPTS / "run_llm_eval_full.py"),
            "--scenarios",
            "A,B,C,D,E,F,G,H,X",
        ],
        "Phase 2b full 120 eval",
    )

    print("\n# V2 Pipeline Complete")
    print(f"Decision: {decision_path}")
    print(f"Full summary: {EVAL_DIR / 'llm_eval_full_summary.md'}")
    print(f"Action items: {EVAL_DIR / 'phase2_action_items.md'}")
    print(f"END {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
