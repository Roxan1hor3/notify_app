from asyncio import AbstractEventLoop

import aiomysql
from aiomysql import Connection
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.uri_parser import parse_uri


async def get_my_sql_db_connection(
    host: str, port: int, user: str, password: str, db: str, loop: AbstractEventLoop
) -> Connection:
    connection = await aiomysql.connect(
        host=host, port=port, user=user, password=password, db=db, loop=loop
    )
    return connection


def create_mongo_connection(db_url: str) -> AsyncIOMotorClient:
    """Mongo DB factory
    :param db_url: [description]
    :type db_url: str
    """
    client = AsyncIOMotorClient(db_url)
    db_config = parse_uri(db_url)
    return client[db_config["database"]]
