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

    async def get_notify_count(self, username: str = None):
        return await self.collection.count_documents(
            {} if username is None else {"username": username}
        )

    async def get_list(self, ordering: str, limit, offset, username: str = None):
        results = (
            await self.collection.find(
                {} if username is None else {"username": username}
            )
            .limit(limit=limit)
            .skip(skip=offset)
            .sort(ordering.lstrip("-"), -1 if ordering.startswith("-") else 1)
            .to_list(length=None)
        )
        return [self.MODEL(**res) for res in results]
