from motor.core import AgnosticClientSession
from pymongo import InsertOne

from src.notify.adapters.models.message import Message
from src.notify.adapters.queries.message_query import MessageQueryStorage
from src.notify.adapters.repos.base import BaseMotorRepo


class MessageRepo(BaseMotorRepo):
    MODEL = Message
    query_storage = MessageQueryStorage()

    async def init_indexes(self):
        await self.collection.create_index([("notify_uuid", 1)])
        await self.collection.create_index([("user_uuid", 1)])

    async def bulk_save_messages(
        self, messages: list[Message], session: AgnosticClientSession
    ) -> list[Message]:
        bulk_messages_inserts = [
            InsertOne(document=message.model_dump()) for message in messages
        ]
        count = len(bulk_messages_inserts)
        limit = 100
        for offset in range(0, count, limit):
            await self.bulk_write(bulk_messages_inserts[offset: offset+limit], session=session),
        return messages
