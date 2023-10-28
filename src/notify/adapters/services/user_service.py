import logging
from typing import Self

from aiomysql import Connection

from src.notify.adapters.repos.user_repo import UsersRepo
from src.notify.adapters.services.base import BaseService

logger = logging.getLogger(__name__)


class UserService(BaseService):
    @classmethod
    async def create_service(
        cls,
        mysql_db_connection: Connection,
    ) -> Self:
        self = cls()

        self.user_repo = await UsersRepo.create_repo(mysql_db_connection)

        return self
