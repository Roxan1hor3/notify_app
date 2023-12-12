from src.notify.adapters.models.telegram_connection_request import (
    TelegramConnectionRequest,
)
from src.notify.adapters.queries.telegram_connection_request_query import (
    TelegramConnectionRequestQuery,
)
from src.notify.adapters.repos.base import BaseMotorRepo


class TelegramConnectionRequestRepo(BaseMotorRepo):
    MODEL = TelegramConnectionRequest
    query_storage = TelegramConnectionRequestQuery()

    async def init_indexes(self):
        await self.collection.create_index([("chat_id", 1)])

    async def save_connection_request(
        self, telegram_connection_request: TelegramConnectionRequest
    ) -> TelegramConnectionRequest:
        await self.collection.insert_one(telegram_connection_request.model_dump())
        return telegram_connection_request
