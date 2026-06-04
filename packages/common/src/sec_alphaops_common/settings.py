from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class BaseServiceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql+asyncpg://alphaops:alphaops@localhost:5432/alphaops"
    database_read_url: str | None = None
    redis_url: str = "redis://localhost:6379/0"
    temporal_address: str = "localhost:7233"
    temporal_namespace: str = "default"
    temporal_task_queue: str = "sec-alphaops"
    # Temporal Cloud: set address, namespace, and API key (TLS is enabled when api_key is set)
    temporal_api_key: str | None = None
    r2_endpoint: str | None = None
    r2_bucket: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_access_key: str | None = None
    sec_edgar_identity: str = "SEC AlphaOps dev@example.com"
    llm_provider: str = "ollama"
    openai_api_key: str | None = None
    ollama_base_url: str = "http://localhost:11434"

    @property
    def read_database_url(self) -> str:
        return self.database_read_url or self.database_url

    @property
    def use_r2(self) -> bool:
        return bool(self.r2_endpoint and self.r2_bucket and self.r2_access_key_id)
