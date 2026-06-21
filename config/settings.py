import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
WORKSPACE_DIR = PROJECT_ROOT / "data" / "workspace"
FORETELL_SKILLS_DIR = PROJECT_ROOT / "foretell" / "skills"

DEFAULT_MODEL = os.environ.get("MINIMAX_MODEL", "MiniMax-M3")
DEFAULT_BASE_URL = os.environ.get("MINIMAX_BASE_URL", "https://api.minimaxi.com/v1")

LANGSMITH_TRACING = os.environ.get("LANGSMITH_TRACING", "false").lower() == "true"
LANGSMITH_PROJECT = os.environ.get("LANGSMITH_PROJECT", "foretell")


@dataclass(frozen=True)
class Settings:
    deploy_env: str
    database_url: str | None
    crazy_sports_api_base: str | None
    crazy_sports_api_key: str | None
    api_host: str
    api_port: int
    jwt_secret: str

    @property
    def is_dev(self) -> bool:
        return self.deploy_env == "dev"

    @property
    def is_prod(self) -> bool:
        return self.deploy_env == "prod"


def _load_settings() -> Settings:
    deploy_env = os.environ.get("DEPLOY_ENV", "dev").lower()
    if deploy_env not in {"dev", "prod"}:
        raise ValueError(f"DEPLOY_ENV must be 'dev' or 'prod', got {deploy_env!r}")

    return Settings(
        deploy_env=deploy_env,
        database_url=os.environ.get("DATABASE_URL") or None,
        crazy_sports_api_base=os.environ.get("CRAZY_SPORTS_API_BASE") or None,
        crazy_sports_api_key=os.environ.get("CRAZY_SPORTS_API_KEY") or None,
        api_host=os.environ.get("API_HOST", "127.0.0.1"),
        api_port=int(os.environ.get("API_PORT", "8000")),
        jwt_secret=os.environ.get("JWT_SECRET", "dev-jwt-secret-change-me"),
    )


@lru_cache
def get_settings() -> Settings:
    return _load_settings()
