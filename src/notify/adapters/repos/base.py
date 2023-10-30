from abc import ABC
from contextlib import asynccontextmanager
from typing import Self, Type

import aiomysql
from aiomysql import Connection
from pydantic import BaseModel

from src.notify.adapters.queries.base import BaseQueriesStorage


class BaseRepository(ABC):
    def __init__(self):
        """Base repo constructor"""


class BaseMySqlRepo(BaseRepository):
    MODEL: Type[BaseModel]
    query_storage = BaseQueriesStorage()
    connection: Connection

    def __init__(self) -> None:
        super().__init__()
        self._collection = None

    @classmethod
    async def create_repo(cls, connection: Connection) -> Self:
        """Asynchronous repository initialization"""
        repo = cls()
        repo.connection = connection
        return repo

    @asynccontextmanager
    async def get_cursor(self) -> None:
        cursor = await self.connection.cursor(aiomysql.DictCursor)
        yield cursor
        await cursor.close()
