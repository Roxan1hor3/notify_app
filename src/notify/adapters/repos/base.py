from abc import ABC
from contextlib import contextmanager
from typing import Self, Type

from aiomysql import Connection
from sqlalchemy.ext.asyncio import AsyncSession


class BaseRepository(ABC):
    def __init__(self):
        """Base repo constructor"""


class BaseMySqlRepo(BaseRepository):
    MODEL: Type[BaseMySqlEntityModel]
    query_storage = BaseMySqlQueries()
    connection: Connection

    def __init__(self) -> None:
        super().__init__()
        self._collection = None

    @classmethod
    async def create_repo(cls, session: AsyncSession) -> Self:
        """Asynchronous repository initialization"""
        repo = cls()
        repo.session = session
        return repo

    @contextmanager
    async def get_cursor(self) -> None:
        async with self.connection.cursor() as cur:
            yield cur
