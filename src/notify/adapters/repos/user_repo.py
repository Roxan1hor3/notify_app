from src.notify.adapters.models.user import User
from src.notify.adapters.repos.base import BaseMySqlRepo


class UsersRepo(BaseMySqlRepo):
    async def get_list(self, retrieve_args: RetrieveManyArgs) -> tuple[int, list[User]]:
        async with self.get_cursor() as cur:
            count = await cur.execute(self.query_storage.get_users_count(match_params))
            results = await cur.execute(self.query_storage.get_users(match_params))
            return count, [self.MODEL(**res) for res in results]
