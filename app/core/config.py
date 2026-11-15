from functools import lru_cache
from urllib.parse import quote_plus

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings, loaded from environment variables / .env file."""

    APP_NAME: str = "Smart Form Builder API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "form_builder"

    # Auth
    SECRET_KEY: str = "change-this-secret-key-in-env"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Frontend / project info
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    PROJECT_TITLE: str = (
        "Development of a Dynamic Workflow Automation System Using a Digital Data Collection Framework"
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def DATABASE_URL(self) -> str:
        user = quote_plus(self.DB_USER)
        password = quote_plus(self.DB_PASSWORD)
        return (
            f"postgresql+psycopg2://{user}:{password}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
