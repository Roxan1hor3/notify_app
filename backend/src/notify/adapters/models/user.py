import hashlib
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator

from backend.src.notify.adapters.models.base import BaseEntityModel


def _default_uuid():
    return uuid4()


class User(BaseEntityModel):
    uuid: Annotated[UUID, Field(default_factory=_default_uuid)]
    username: str
    password: str
    session_uuid: UUID | None = None
    last_login_date: datetime | None = None
    expire_time: datetime | None = None

    @staticmethod
    def get_entity_name():
        return "admin_users"


class TempUser(BaseModel):
    username: str
    password: str

    @field_validator("password", mode="after")
    def hash_password(cls, value: str) -> str:
        return hashlib.md5(value.encode()).hexdigest()


class UserFilter(BaseModel):
    session_uuid: UUID | None = None
    username: str | None = None
    expire_time_lt: datetime | None = None
