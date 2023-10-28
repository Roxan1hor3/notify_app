from asyncio import AbstractEventLoop

from aiomysql import create_pool
from motor.motor_asyncio import AsyncIOMotorClient


async def get_my_sql_db_connection(
    host: str, port: int, user: str, password: str, db: str, loop: AbstractEventLoop
) -> AsyncIOMotorClient:
    pool = await create_pool(
        host=host, port=port, user=user, password=password, db=db, loop=loop
    )
    async with pool.acquire() as conn:
        yield conn
