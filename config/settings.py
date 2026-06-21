import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")
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
    crazy_sports_data_source: str
    crazy_sports_api_base: str | None
    crazy_sports_api_key: str | None
    mysql_host: str | None
    mysql_port: int
    mysql_user: str | None
    mysql_password: str | None
    mysql_database: str | None
    api_host: str
    api_port: int
    jwt_secret: str

    @property
    def is_dev(self) -> bool:
        return self.deploy_env == "dev"

    @property
    def is_prod(self) -> bool:
        return self.deploy_env == "prod"

    @property
    def mysql_configured(self) -> bool:
        return bool(
            self.mysql_host
            and self.mysql_user
            and self.mysql_password
            and self.mysql_database
        )

    def mysql_connection_kwargs(self) -> dict:
        if not self.mysql_configured:
            raise ValueError("MySQL 未配置完整")
        return {
            "host": self.mysql_host,
            "port": self.mysql_port,
            "user": self.mysql_user,
            "password": self.mysql_password,
            "database": self.mysql_database,
            "charset": "utf8mb4",
            "connect_timeout": 10,
            "read_timeout": 30,
        }


def _load_settings() -> Settings:
    deploy_env = os.environ.get("DEPLOY_ENV", "dev").lower()
    if deploy_env not in {"dev", "prod"}:
        raise ValueError(f"DEPLOY_ENV must be 'dev' or 'prod', got {deploy_env!r}")

    data_source = os.environ.get("CRAZY_SPORTS_DATA_SOURCE", "mock").lower()
    if data_source not in {"mock", "mysql"}:
        raise ValueError(
            f"CRAZY_SPORTS_DATA_SOURCE must be 'mock' or 'mysql', got {data_source!r}"
        )

    return Settings(
        deploy_env=deploy_env,
        database_url=os.environ.get("DATABASE_URL") or None,
        crazy_sports_data_source=data_source,
        crazy_sports_api_base=os.environ.get("CRAZY_SPORTS_API_BASE") or None,
        crazy_sports_api_key=os.environ.get("CRAZY_SPORTS_API_KEY") or None,
        mysql_host=os.environ.get("MYSQL_HOST") or None,
        mysql_port=int(os.environ.get("MYSQL_PORT", "3306")),
        mysql_user=os.environ.get("MYSQL_USER") or None,
        mysql_password=os.environ.get("MYSQL_PASSWORD") or None,
        mysql_database=os.environ.get("MYSQL_DATABASE") or None,
        api_host=os.environ.get("API_HOST", "127.0.0.1"),
        api_port=int(os.environ.get("API_PORT", "8000")),
        jwt_secret=os.environ.get("JWT_SECRET", "dev-jwt-secret-change-me"),
    )


@lru_cache
def get_settings() -> Settings:
    return _load_settings()
