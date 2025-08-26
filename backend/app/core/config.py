from pydantic import (
    PostgresDsn,
    computed_field,
    BeforeValidator,
    AnyUrl
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from functools import lru_cache
import secrets
from typing import Annotated, Any, Literal, Union

BASE_DIR = Path(__file__).resolve().parent.parent

def parse_cors(v: Any) -> list[str] | str:
    if isinstance(v, str) and not v.startswith("["):
        return [i.strip() for i in v.split(",")]
    elif isinstance(v, (list, str)):
        return v
    raise ValueError(v)
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file = BASE_DIR / "../.env")
    APP_NAME: str = "FastVue FullStack Template"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DB_DEBUG: bool = False
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str
    DB_USERNAME: str
    DB_PASSWORD: str
    API_PATH: str = "/api"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8 # 60 minutes * 24 hours * 8 days = 8 days
    ALGORITHM: str = "HS256"
    FRONTEND_HOST: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: Annotated[
        Union[list[AnyUrl], str], BeforeValidator(parse_cors)
    ] = []
    # Database health and error handling
    DATABASE_HEALTH_CHECK_ON_STARTUP: bool = True
    DATABASE_CONNECTION_TIMEOUT: int = 30
    DATABASE_POOL_PRE_PING: bool = True

    @computed_field  # type: ignore[prop-decorator]
    @property
    def all_cors_origins(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.BACKEND_CORS_ORIGINS] + [
            self.FRONTEND_HOST
        ]

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