from asyncio import AbstractEventLoop

import aiomysql
from aiomysql import Connection


async def get_my_sql_db_connection(
    host: str, port: int, user: str, password: str, db: str, loop: AbstractEventLoop
) -> Connection:
    connection = await aiomysql.connect(
        host=host, port=port, user=user, password=password, db=db, loop=loop
    )
    return connection
