import logging
from abc import ABC
from contextlib import asynccontextmanager
from typing import Type

import aiomysql
from aiomysql import Connection
from motor.core import AgnosticClientSession
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorDatabase
from pydantic import BaseModel
from pymongo import DeleteMany, InsertOne, ReplaceOne, UpdateMany, UpdateOne
from pymongo.errors import BulkWriteError

from src.notify.adapters.models.base import BaseEntityModel
from src.notify.adapters.queries.base import BaseQueriesStorage

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    def __init__(self):
        """Base repo constructor"""


class BaseAioMySqlRepo(BaseRepository):
    MODEL: Type[BaseModel]
    query_storage = BaseQueriesStorage()
    connection: Connection

    def __init__(self) -> None:
        super().__init__()
        self._collection = None

    @classmethod
    async def create_repo(cls, connection: Connection):
        """Asynchronous repository initialization"""
        repo = cls()
        repo.connection = connection
        return repo

    @asynccontextmanager
    async def get_cursor(self) -> None:
        cursor = await self.connection.cursor(aiomysql.DictCursor)
        yield cursor
        await cursor.close()


class BaseMotorRepo(BaseRepository):
    MODEL: Type[BaseEntityModel]
    database: AsyncIOMotorDatabase
    query_storage = BaseQueriesStorage()

    def __init__(self) -> None:
        super().__init__()
        self._collection = None

    @classmethod
    async def create_repo(cls, db_connection: AsyncIOMotorDatabase):
        """Asynchronous repository initialization"""
        repo = cls()
        repo.database = db_connection
        await repo.init_indexes()
        return repo

    async def init_indexes(self):
        """Init repo indexes"""
        raise NotImplementedError

    @property
    def collection(self) -> AsyncIOMotorCollection:
        if self._collection is None:
            collection_name = self.MODEL.get_entity_name()
            self._collection = self.database[collection_name]
        return self._collection

    @asynccontextmanager
    async def start_transaction(self):
        async with await self.database.client.start_session() as s:
            async with s.start_transaction():
                yield s

    async def bulk_write(
        self,
        update_list: list[InsertOne | DeleteMany | ReplaceOne | UpdateOne | UpdateMany],
        session: AgnosticClientSession = None,
        raise_error: bool = False,
    ) -> None:
        if update_list:
            try:
                await self.collection.bulk_write(update_list, session=session)
            except BulkWriteError as bwe:
                logger.critical("Failed offer update")
                messages = [err["errmsg"] for err in bwe.details["writeErrors"]]
                logger.critical("; ".join(messages))
                if raise_error is True:
                    raise bwe
