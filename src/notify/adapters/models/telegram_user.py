from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field


def _default_datetime():
    return datetime.now()


class TelegramUser(BaseModel):
    chat_id: int
    first_name: str
    last_name: str | None
    username: str | None
    personal_account_id: int | None = None
    billing_id: int | None = None
    phone_number: str | None = None
    created_at: Annotated[datetime, Field(default_factory=_default_datetime)]
    updated_at: Annotated[datetime, Field(default_factory=_default_datetime)]

    @staticmethod
    def get_entity_name():
        return "telegram_users"
