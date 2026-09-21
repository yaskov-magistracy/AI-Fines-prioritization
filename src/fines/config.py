from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["local", "ci", "prod"] = "local"
    log_level: str = "INFO"

    database_url: str = "sqlite+aiosqlite:///./fines.db"
    storage_dir: Path = Path("./storage")

    extractor_backend: Literal["rule_based", "llm"] = "rule_based"
    price_provider: Literal["stub", "http"] = "stub"

    price_api_base_url: str = ""
    price_api_key: str = Field(default="", repr=False)

    llm_base_url: str = ""
    llm_api_key: str = Field(default="", repr=False)
    llm_model: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
