from datetime import datetime
from enum import StrEnum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import Field

from src.notify.adapters.models.base import BaseEntityModel


def _default_uuid():
    return uuid4()


def _default_datetime():
    return datetime.now()


class MessageStatus(StrEnum):
    SANDED = "Повідомлення відправленно"
    NOT_VALID_PHONE_NUMBER = "Не валідний номер телефона"
    PHONE_NUMBER_IS_REPEATED = "Номер телефона дуплікований"
    UNEXPECTED_ERROR = "Не відома помилка повторіть відправку"
    NOT_REGISTERED_TELEGRAM = "Абонент не підписаний на телеграм бота"


class Message(BaseEntityModel):
    uuid: Annotated[UUID, Field(default_factory=_default_uuid)]
    notify_uuid: UUID
    user_id: int
    phone_number: str | None = None
    telegram_chat_id: int | None = None
    created_at: Annotated[datetime, Field(default_factory=_default_datetime)]
    status: MessageStatus

    @staticmethod
    def get_entity_name():
        return "messages"
