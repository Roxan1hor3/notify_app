from functools import lru_cache
from os.path import abspath, dirname, join
from typing import Sequence

from pydantic_settings import BaseSettings, SettingsConfigDict


class TurboSMSConfig(BaseSettings):
    wsdl: str
    login: str
    password: str


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
    MY_SQL_DB_CHARSET: str

    MONGO_DB_URL: str

    USE_DOCS: bool = False

    CORS_ALLOW_ORIGINS: Sequence[str] = ()
    CORS_ALLOW_METHODS: Sequence[str] = ("GET",)
    CORS_ALLOW_HEADERS: Sequence[str] = ()
    CORS_ALLOW_CREDENTIALS: bool = False

    LOG_LEVEL: str = "INFO"

    SMS_SENDER: str
    TURBO_SMS_CONFIG: TurboSMSConfig
    USE_SSO: bool = False

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
