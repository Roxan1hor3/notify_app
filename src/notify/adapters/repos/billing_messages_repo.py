from src.notify.adapters.models.message_billing import MessageBilling
from src.notify.adapters.queries.billing_messages_query import (
    MessageBillingQueryStorage,
)
from src.notify.adapters.repos.base import BaseAioMySqlRepo


class MessagesBillingRepo(BaseAioMySqlRepo):
    MODEL = MessageBilling
    query_storage = MessageBillingQueryStorage()

    async def get_list(
        self,
        created_since_from: float,
        created_since_to: float,
        limit: int,
        offset: int,
    ) -> list[MessageBilling]:
        async with self.get_cursor() as cur:
            await cur.execute(
                self.query_storage.get_messages(
                    created_since_from=created_since_from,
                    created_since_to=created_since_to,
                    limit=limit,
                    offset=offset,
                ).get_sql()
            )
            results = await cur.fetchall()
            return [self.MODEL(**res) for res in results]

    async def get_messages_count(
        self, created_since_from: float, created_since_to: float
    ) -> int:
        async with self.get_cursor() as cur:
            await cur.execute(
                self.query_storage.get_messages_count(
                    created_since_from=created_since_from,
                    created_since_to=created_since_to,
                ).get_sql()
            )
            result = await cur.fetchall()
            return result[0]["count"]
