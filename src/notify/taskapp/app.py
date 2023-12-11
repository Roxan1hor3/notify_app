from asyncio import get_event_loop
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable

from celery import Celery
from celery.schedules import crontab

from src.notify.adapters.services.notify_service import NotifyService
from src.notify.adapters.services.telegram_service import TelegramService
from src.notify.adapters.services.user_service import UserService
from src.notify.config import get_settings
from src.notify.extensions.db import (
    create_mongo_connection,
    get_my_sql_db_connection_pool,
)
from src.notify.taskapp.service_manager import (
    init_celery_service_manager,
    service_manager,
)


@dataclass
class AppContext:
    notify_service: NotifyService = None
    telegram_service: TelegramService = None
    user_service: UserService = None


class CeleryApp(Celery):
    ctx: AppContext = None


settings = get_settings()
_app = CeleryApp(__name__, broker=settings.CELERY_BROKER_URL)


def create_celery_app():
    task_modules = ["telegram_tasks"]
    _app.autodiscover_tasks(
        [f"src.notify.taskapp.tasks.{task_module}" for task_module in task_modules]
    )
    loop = get_event_loop()
    loop.run_until_complete(
        init_celery_service_manager(
            settings=settings,
            my_sql_connection_pool=loop.run_until_complete(
                get_my_sql_db_connection_pool(
                    host=settings.MY_SQL_DB_HOST,
                    port=settings.MY_SQL_DB_PORT,
                    user=settings.MY_SQL_DB_USER,
                    password=settings.MY_SQL_DB_PASSWORD,
                    db=settings.MY_SQL_DB_NAME,
                    loop=get_event_loop(),
                    charset=settings.MY_SQL_DB_CHARSET,
                )
            ),
            mongo_db_connection=create_mongo_connection(db_url=settings.MONGO_DB_URL),
        )
    )
    _app.ctx = AppContext()
    _app.ctx.notify_service = loop.run_until_complete(service_manager.notify_service)
    _app.ctx.telegram_service = loop.run_until_complete(
        service_manager.telegram_service
    )
    _app.ctx.user_service = loop.run_until_complete(service_manager.user_service)
    return _app


def async_run_task(task) -> Callable[[tuple[Any, ...], dict[str, Any]], None]:
    @_app.task
    @wraps(task)
    def wrapper(*args, **kwargs) -> None:
        get_event_loop().run_until_complete(task(_app.ctx, *args, **kwargs))

    return wrapper


_app.conf.beat_schedule = {
    "send_billing_messages_in_telegram": {
        "task": "src.notify.taskapp.tasks.telegram_tasks.send_billing_messages_in_telegram",
        "schedule": crontab(minute="*/5"),
    },
}
