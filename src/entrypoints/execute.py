import asyncio
import logging
from asyncio import new_event_loop

import typer

from src.notify.api.dependencies.auth import UserService
from src.notify.config import get_settings
from src.notify.extensions.db import (
    create_mongo_connection,
    get_my_sql_db_connection_pool,
)

app = typer.Typer()


@app.command(name="users_update")
def users_update():
    service = loop.run_until_complete(
        UserService.create_service(
            mongo_db_connection=mongo_db_connection,
            mysql_db_pool=db_my_sql_pool,
            static_dir_path=settings.STATIC_DIR,
        )
    )
    loop.run_until_complete(service.upload_new_users())


if __name__ == "__main__":
    settings = get_settings()
    static_dir_path = settings.STATIC_DIR
    loop = new_event_loop()
    asyncio.set_event_loop(loop)
    # first set_event_loop because motor has own event loop
    db_my_sql_pool = loop.run_until_complete(
        get_my_sql_db_connection_pool(
            host=settings.MY_SQL_DB_HOST,
            port=settings.MY_SQL_DB_PORT,
            user=settings.MY_SQL_DB_USER,
            password=settings.MY_SQL_DB_PASSWORD,
            db=settings.MY_SQL_DB_NAME,
            loop=loop,
        )
    )
    mongo_db_connection = create_mongo_connection(db_url=settings.MONGO_DB_URL)

    logger = logging.getLogger(__name__)
    app()
    loop.close()
