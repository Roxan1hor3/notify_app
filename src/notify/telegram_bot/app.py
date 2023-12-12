import logging
from asyncio import get_running_loop
from typing import Any, Awaitable, Callable

from aiogram import Bot, Dispatcher
from aiogram.enums.parse_mode import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import TelegramObject

from src.notify.config import get_settings
from src.notify.extensions.db import (
    create_mongo_connection,
    get_my_sql_db_connection_pool,
)
from src.notify.telegram_bot.dependency.services import (
    init_telegram_bot_service_manager,
    service_manager,
)
from src.notify.telegram_bot.handlers.base import base_router
from src.notify.telegram_bot.handlers.connection_request import (
    connection_request_router,
)
from src.notify.telegram_bot.handlers.contacts import contact_router
from src.notify.telegram_bot.handlers.payment import payment_router
from src.notify.telegram_bot.handlers.repair_request import repair_request_router
from src.notify.telegram_bot.handlers.start import start_router
from src.notify.telegram_bot.handlers.tariffs import tariffs_router


async def main():
    settings = get_settings()
    logging.basicConfig(level=settings.LOG_LEVEL)
    await init_telegram_bot_service_manager(
        settings=settings,
        my_sql_connection_pool=await get_my_sql_db_connection_pool(
            host=settings.MY_SQL_DB_HOST,
            port=settings.MY_SQL_DB_PORT,
            user=settings.MY_SQL_DB_USER,
            password=settings.MY_SQL_DB_PASSWORD,
            db=settings.MY_SQL_DB_NAME,
            loop=get_running_loop(),
            charset=settings.MY_SQL_DB_CHARSET,
        ),
        mongo_db_connection=create_mongo_connection(db_url=settings.MONGO_DB_URL),
    )
    bot = Bot(
        token=settings.TELEGRAM_BOT_TOKEN,
        parse_mode=ParseMode.HTML,
    )
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(base_router)
    dp.include_router(contact_router)
    dp.include_router(tariffs_router)
    dp.include_router(repair_request_router)
    dp.include_router(connection_request_router)
    dp.include_router(payment_router)
    dp.include_router(start_router)

    @dp.message.outer_middleware()
    async def add_services_middleware(
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        data["notify_service"] = await service_manager.notify_service
        data["user_service"] = await service_manager.user_service
        data["telegram_service"] = await service_manager.telegram_service
        return await handler(event, data)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
