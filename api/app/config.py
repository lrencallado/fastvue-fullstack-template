from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    app_name: str = "FastNuxt"
    db_host: str = "127.0.0.1"
    db_port: str = "5432"
    db_name: str
    db_username: str
    db_password: str
    model_config = SettingsConfigDict(env_file = BASE_DIR / ".env")

@lru_cache
def get_settings():
    return Settings()

SETTINGS = get_settings()

DATABASE_URI = f"postgresql+asyncpg://{SETTINGS.db_username}:{SETTINGS.db_password}@{SETTINGS.db_host}:{SETTINGS.db_port}/{SETTINGS.db_name}"