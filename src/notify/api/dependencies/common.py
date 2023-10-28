from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.notify.config import Settings, get_settings


async def get_my_sql_db_conn(
    settings: Settings = Depends(get_settings),
) -> AsyncIOMotorDatabase:
    return get_db_connection(
        db_url=settings.DB_URL,
    )
