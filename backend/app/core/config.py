from pydantic import (
    PostgresDsn,
    computed_field
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from functools import lru_cache
import secrets
from typing import Annotated, Any, Literal

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "FastVue FullStack Template"
    APP_ENV: Literal["local", "staging", "production"] = "local"
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USERNAME: str
    DB_PASSWORD: str
    API_PATH: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 60 minutes * 24 hours * 8 days = 8 days
    ALGORITHM: str = "HS256"
    model_config = SettingsConfigDict(env_file = BASE_DIR / "../.env")

    @computed_field
    @property
    def SQLALCHEMY_DATABASE_URI(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme="postgresql+asyncpg",
            username=self.DB_USERNAME,
            password=self.DB_PASSWORD,
            host=self.DB_HOST,
            port=self.DB_PORT,
            path=self.DB_NAME,
        )

@lru_cache
def get_settings():
    return Settings()

settings = get_settings()

print(settings.SQLALCHEMY_DATABASE_URI)