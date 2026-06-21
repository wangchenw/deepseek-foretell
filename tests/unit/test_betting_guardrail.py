"""购彩护栏 prompt / Skill 单元测试。"""

from pathlib import Path

from config.settings import FORETELL_SKILLS_DIR
from foretell.prompts import SYSTEM_PROMPT

GUARDRAIL_TEXT = "⚠️ 彩票有风险，投注需谨慎"


def test_system_prompt_contains_guardrail_hint() -> None:
    assert "彩票有风险" in SYSTEM_PROMPT
    assert "投注需谨慎" in SYSTEM_PROMPT


def test_betting_single_skill_requires_guardrail() -> None:
    content = Path(FORETELL_SKILLS_DIR / "foretell-betting-single" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert GUARDRAIL_TEXT in content
    assert "单一" in content or "单一明确" in content


def test_batch_screening_skill_requires_guardrail() -> None:
    content = Path(FORETELL_SKILLS_DIR / "foretell-batch-screening" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert GUARDRAIL_TEXT in content


def test_output_discipline_guardrail() -> None:
    content = Path(FORETELL_SKILLS_DIR / "foretell-output-discipline" / "SKILL.md").read_text(
        encoding="utf-8"
    )
    assert GUARDRAIL_TEXT in content
