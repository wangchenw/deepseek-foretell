"""Shared pytest fixtures for Foretell."""

from __future__ import annotations

import pytest

from config.settings import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    """Isolate settings singleton between tests."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def dev_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Force DEPLOY_ENV=dev for backend factory tests."""
    monkeypatch.setenv("DEPLOY_ENV", "dev")
    get_settings.cache_clear()
