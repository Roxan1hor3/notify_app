from datetime import datetime
from typing import Annotated

from pydantic import Field

from src.notify.adapters.models.base import BaseEntityModel


def _default_datetime():
    return datetime.now()


class TelegramRepairRequest(BaseEntityModel):
    chat_id: int
    fio: str
    address: str
    phone_number: str
    problem: str
    created_at: Annotated[datetime, Field(default_factory=_default_datetime)]

    @staticmethod
    def get_entity_name():
        return "telegram_repair_request"
