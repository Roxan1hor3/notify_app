from motor.core import AgnosticClientSession

from src.notify.adapters.models.notify import Notify
from src.notify.adapters.queries.notify_query import NotifyQueryStorage
from src.notify.adapters.repos.base import BaseMotorRepo


class NotifyRepo(BaseMotorRepo):
    MODEL = Notify
    query_storage = NotifyQueryStorage()

    async def init_indexes(self):
        await self.collection.create_index([("username", 1)])

    async def save_notify(
            self, notify: Notify, session: AgnosticClientSession
    ) -> Notify:
        await self.collection.insert_one(notify.model_dump(), session=session)
        return notify
