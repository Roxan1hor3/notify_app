from src.notify.adapters.models.telegram_repair_request import TelegramRepairRequest
from src.notify.adapters.queries.telegram_repair_request_query import (
    TelegramRepairRequestQuery,
)
from src.notify.adapters.repos.base import BaseMotorRepo


class TelegramRepairRequestRepo(BaseMotorRepo):
    MODEL = TelegramRepairRequest
    query_storage = TelegramRepairRequestQuery()

    async def init_indexes(self):
        await self.collection.create_index([("chat_id", 1)])

    async def save_repair_request(
        self, telegram_repair_request: TelegramRepairRequest
    ) -> TelegramRepairRequest:
        await self.collection.insert_one(telegram_repair_request.model_dump())
        return telegram_repair_request
