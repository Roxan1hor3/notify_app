from asyncio import get_running_loop

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.notify.config import Settings, get_settings
from src.notify.extensions.db import (
    create_mongo_connection,
    get_my_sql_db_connection_pool,
)


async def get_my_sql_db_conn_pool(
    settings: Settings = Depends(get_settings),
) -> AsyncIOMotorDatabase:
    return await get_my_sql_db_connection_pool(
        host=settings.MY_SQL_DB_HOST,
        port=settings.MY_SQL_DB_PORT,
        user=settings.MY_SQL_DB_USER,
        password=settings.MY_SQL_DB_PASSWORD,
        db=settings.MY_SQL_DB_NAME,
        loop=get_running_loop(),
        charset=settings.MY_SQL_DB_CHARSET,
    )


async def get_mongo_conn(
    settings: Settings = Depends(get_settings),
) -> AsyncIOMotorDatabase:
    return create_mongo_connection(db_url=settings.MONGO_DB_URL)
