from src.notify.adapters.models.user import User, UserFilter
from src.notify.adapters.queries.users_query import UserQueryStorage
from src.notify.adapters.repos.base import BaseMySqlRepo


class UsersRepo(BaseMySqlRepo):
    MODEL = User
    query_storage = UserQueryStorage()

    async def get_list(
        self, _filter: UserFilter, limit: int, offset: int, ordering: str
    ) -> tuple[int, list[User]]:
        async with self.get_cursor() as cur:
            await cur.execute(
                self.query_storage.get_users_count(_filter=_filter).get_sql()
            )
            count = await cur.fetchall()
            await cur.execute(
                self.query_storage.get_users(
                    _filter=_filter, limit=limit, offset=offset, ordering=ordering
                ).get_sql()
            )
            results = await cur.fetchall()
            return count, [self.MODEL(**res) for res in results]

    async def get_users_count(self, _filter: UserFilter):
        async with self.get_cursor() as cur:
            await cur.execute(
                self.query_storage.get_users_count(_filter=_filter).get_sql()
            )
            return await cur.fetchall()
