from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(default="sqlite+aiosqlite:///./local.db")

    databricks_host: str | None = None
    databricks_token: str | None = None

    volume_root: str = Field(default="/Volumes/main/velocia/uploads")

    agent_api_base: str = Field(default="http://localhost:9000")
    agent_api_token: str = Field(default="dev-fake-token")

    dev_fake_user_email: str | None = None
    dev_fake_user_name: str | None = None

    log_level: str = Field(default="INFO")
    allowed_file_mime: str = Field(
        default="application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain,text/markdown"
    )
    max_upload_bytes: int = Field(default=52_428_800)

    @property
    def allowed_mime_set(self) -> set[str]:
        return {m.strip() for m in self.allowed_file_mime.split(",") if m.strip()}


settings = Settings()
