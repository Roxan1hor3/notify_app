from src.notify.adapters.models.user_billing import (
    BillingGroup,
    BillingPacket,
    UserBilling,
    UserBillingFilter,
)
from src.notify.adapters.queries.users_billing_query import UserBillingQueryStorage
from src.notify.adapters.repos.base import BaseAioMySqlRepo


class UsersBillingRepo(BaseAioMySqlRepo):
    MODEL = UserBilling
    query_storage = UserBillingQueryStorage()

    async def get_list(
        self, _filter: UserBillingFilter, limit: int, offset: int
    ) -> list[UserBilling]:
        async with self.get_cursor() as cur:
            await cur.execute(
                self.query_storage.get_users(
                    _filter=_filter, limit=limit, offset=offset
                ).get_sql()
            )
            results = await cur.fetchall()
            return [self.MODEL(**res) for res in results]

    async def get_users_count(self, _filter: UserBillingFilter):
        async with self.get_cursor() as cur:
            await cur.execute(
                self.query_storage.get_users_count(_filter=_filter).get_sql()
            )
            result = await cur.fetchall()
            return result[0]["count"]

    async def get_groups_filters(self):
        async with self.get_cursor() as cur:
            await cur.execute(self.query_storage.get_groups().get_sql())
            results = await cur.fetchall()
            return [BillingGroup(**res) for res in results]

    async def get_packets_filters(self):
        async with self.get_cursor() as cur:
            await cur.execute(self.query_storage.get_packets().get_sql())
            results = await cur.fetchall()
            return [BillingPacket(**res) for res in results]
