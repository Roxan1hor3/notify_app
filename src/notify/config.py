from functools import lru_cache
from os.path import abspath, dirname, join
from typing import Sequence

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_RELOAD: bool = True
    PROJECT_PATH: str = dirname(dirname(dirname(abspath(__file__))))
    STATIC_DIR: str = join(PROJECT_PATH, "static")

    MY_SQL_DB_HOST: str
    MY_SQL_DB_USER: str
    MY_SQL_DB_PORT: int
    MY_SQL_DB_PASSWORD: str
    MY_SQL_DB_NAME: str

    MONGO_DB_URL: str

    USE_DOCS: bool = False

    CORS_ALLOW_ORIGINS: Sequence[str] = ()
    CORS_ALLOW_METHODS: Sequence[str] = ("GET",)
    CORS_ALLOW_HEADERS: Sequence[str] = ()
    CORS_ALLOW_CREDENTIALS: bool = False

    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
