"""Phase 3 Skills 存在性与 frontmatter 单元测试。"""

import re
from pathlib import Path

import pytest

from config.settings import FORETELL_SKILLS_DIR

PHASE3_SKILLS = [
    "foretell-post-review",
    "foretell-betting-single",
    "foretell-batch-screening",
    "foretell-odds-query",
    "foretell-league-outlook",
]

CORE_SKILLS = [
    "foretell-entity-resolution",
    "foretell-status-dictionary",
    "foretell-output-discipline",
    "foretell-light-query",
    "foretell-match-analysis",
    "foretell-follow-up",
]

_HAS_CHINESE = re.compile(r"[\u4e00-\u9fff]")


@pytest.mark.parametrize("skill_name", PHASE3_SKILLS + CORE_SKILLS)
def test_skill_exists_with_frontmatter(skill_name: str) -> None:
    skill_path = FORETELL_SKILLS_DIR / skill_name / "SKILL.md"
    assert skill_path.is_file(), f"Missing skill: {skill_name}"

    content = skill_path.read_text(encoding="utf-8")
    assert content.startswith("---"), f"{skill_name} missing YAML frontmatter"
    assert "name:" in content.split("---", 2)[1]
    assert "description:" in content.split("---", 2)[1]
    assert _HAS_CHINESE.search(content), f"{skill_name} should contain Chinese content"
