"""MiniMax LLM 配置单元测试。"""

from __future__ import annotations

import importlib

import pytest


def _reload_llm_modules() -> None:
    import config.llm as llm_mod
    import config.settings as settings_mod

    importlib.reload(settings_mod)
    importlib.reload(llm_mod)


@pytest.fixture(autouse=True)
def _minimax_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINIMAX_API_KEY", "test-key-for-pytest")


def test_thinking_enabled_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MINIMAX_THINKING_ENABLED", raising=False)
    _reload_llm_modules()
    import config.llm as llm_mod

    model = llm_mod.get_chat_model()
    assert model.extra_body == {"thinking": {"type": "adaptive"}}


def test_thinking_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINIMAX_THINKING_ENABLED", "false")
    _reload_llm_modules()
    import config.llm as llm_mod

    model = llm_mod.get_chat_model()
    assert model.extra_body == {"thinking": {"type": "disabled"}}


def test_thinking_enabled_explicit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINIMAX_THINKING_ENABLED", "true")
    _reload_llm_modules()
    import config.llm as llm_mod

    model = llm_mod.get_chat_model()
    assert model.extra_body == {"thinking": {"type": "adaptive"}}
