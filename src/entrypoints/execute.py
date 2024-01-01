import asyncio
import logging
from asyncio import new_event_loop
from datetime import datetime

import pytz
import typer

from src.notify.adapters.services.notify_service import NotifyService
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


@app.command(name="send_billing_messages")
def send_messages():
    print("Enter date to create from in format: %Y-%m-%d %H:M%:%")
    local = pytz.timezone(pytz.utc.zone)
    naive_updated_since = input()
    naive_updated_since = datetime.strptime(naive_updated_since, "%Y-%m-%d %H:M%:%")
    local_updated_since = local.localize(naive_updated_since, is_dst=None)
    created_since_from = local_updated_since.astimezone(pytz.utc)

    print("Enter date to create to in format: %Y-%m-%d %H:M%:%")
    local = pytz.timezone(pytz.utc.zone)
    naive_updated_since = input()
    naive_updated_since = datetime.strptime(naive_updated_since, "%Y-%m-%d %H:M%:%S")
    local_updated_since = local.localize(naive_updated_since, is_dst=None)
    created_since_to = local_updated_since.astimezone(pytz.utc)
    service = loop.run_until_complete(
        NotifyService.create_service(
            my_sql_connection_pool=db_my_sql_pool,
            mongo_db_connection=mongo_db_connection,
            static_dir_path=settings.STATIC_DIR,
            turbo_sms_config=settings.TURBO_SMS_CONFIG,
            sender=settings.SMS_SENDER,
            use_sso=settings.USE_SSO,
            bot_token=settings.TELEGRAM_BOT_TOKEN,
            billing_group_chat_id=settings.BILLING_MESSAGES_TELEGRAM_ID,
        )
    )
    loop.run_until_complete(
        service.send_billing_messages_in_telegram(
            created_since_from=created_since_from, created_since_to=created_since_to
        )
    )


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
            charset=settings.MY_SQL_DB_CHARSET,
        )
    )
    mongo_db_connection = create_mongo_connection(db_url=settings.MONGO_DB_URL)

    logger = logging.getLogger(__name__)
    app()
    loop.close()
