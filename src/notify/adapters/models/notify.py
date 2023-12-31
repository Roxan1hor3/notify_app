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


class NotifyServices(StrEnum):
    TELEGRAM = "Telegram"
    SMS = "SMS"


class Notify(BaseEntityModel):
    uuid: Annotated[UUID, Field(default_factory=_default_uuid)]
    user_uuid: UUID
    username: str
    notify_date: Annotated[datetime, Field(default_factory=_default_datetime)]
    message: str
    sent_by: NotifyServices

    @staticmethod
    def get_entity_name():
        return "notify"
