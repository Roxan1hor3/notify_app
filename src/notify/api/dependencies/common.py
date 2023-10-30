from asyncio import get_running_loop

from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.notify.config import Settings, get_settings
from src.notify.extensions.db import get_my_sql_db_connection


async def get_my_sql_db_conn(
    settings: Settings = Depends(get_settings),
) -> AsyncIOMotorDatabase:
    return await get_my_sql_db_connection(
        user=settings.DB_USER,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        db=settings.DB_NAME,
        password=settings.DB_PASSWORD,
        loop=get_running_loop(),
    )
