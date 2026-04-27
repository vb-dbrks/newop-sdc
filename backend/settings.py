from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- Database ---
    database_url: str = Field(default="sqlite+aiosqlite:///./local.db")

    # --- Databricks SDK (default chain picks up these when set) ---
    databricks_host: str | None = None
    databricks_token: str | None = None

    # --- Volume root for user uploads ---
    volume_root: str = Field(default="/Volumes/main/velocia/uploads")

    # --- Agent API ---
    agent_api_base: str = Field(default="http://localhost:9000")
    agent_api_token: str = Field(default="dev-fake-token")

    # --- Local-dev SSO bypass ---
    dev_fake_user_email: str | None = None
    dev_fake_user_name: str | None = None

    # --- Logging ---
    log_level: str = Field(default="INFO")
    redact_emails_in_logs: bool = Field(default=True)

    # --- File upload constraints ---
    allowed_file_mime: str = Field(
        default="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown"
    )
    max_upload_bytes: int = Field(default=52_428_800)  # 50 MiB

    # --- Caching ---
    obo_cache_ttl_seconds: int = Field(default=45 * 60)

    # --- Idempotency ---
    idempotency_ttl_hours: int = Field(default=24)

    @property
    def allowed_mime_set(self) -> set[str]:
        return {m.strip() for m in self.allowed_file_mime.split(",") if m.strip()}


settings = Settings()
