from aiomysql import Pool
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.notify.adapters.services.notify_service import NotifyService
from src.notify.adapters.services.telegram_service import TelegramService
from src.notify.adapters.services.user_service import UserService
from src.notify.config import Settings


class ServiceManager:
    settings: Settings
    my_sql_connection_pool: Pool
    mongo_db_connection: AsyncIOMotorDatabase

    _user_service: UserService = None
    _notify_service: NotifyService = None
    _telegram_service: TelegramService = None

    async def create(
        self,
        settings: Settings,
        my_sql_connection_pool: Pool,
        mongo_db_connection: AsyncIOMotorDatabase,
    ) -> None:
        self.my_sql_connection_pool = my_sql_connection_pool
        self.mongo_db_connection = mongo_db_connection
        self.settings = settings
        self._user_service = await self._create_user_service(
            my_sql_connection_pool=self.my_sql_connection_pool,
            mongo_db_connection=self.mongo_db_connection,
            settings=self.settings,
        )
        self._notify_service = await self._create_notify_service(
            my_sql_connection_pool=self.my_sql_connection_pool,
            mongo_db_connection=self.mongo_db_connection,
            settings=self.settings,
        )

    async def _create_user_service(
        self,
        my_sql_connection_pool: Pool,
        mongo_db_connection: AsyncIOMotorDatabase,
        settings: Settings,
    ) -> UserService:
        if self._user_service is None:
            self._user_service = await UserService.create_service(
                my_sql_connection_pool, mongo_db_connection, settings.STATIC_DIR
            )
        return self._user_service

    @property
    async def user_service(self):
        return await self._create_user_service(
            my_sql_connection_pool=self.my_sql_connection_pool,
            mongo_db_connection=self.mongo_db_connection,
            settings=self.settings,
        )

    @property
    async def notify_service(self):
        return await self._create_notify_service(
            my_sql_connection_pool=self.my_sql_connection_pool,
            mongo_db_connection=self.mongo_db_connection,
            settings=self.settings,
        )

    @property
    async def telegram_service(self):
        return await self._create_telegram_service(
            my_sql_connection_pool=self.my_sql_connection_pool,
            mongo_db_connection=self.mongo_db_connection,
            settings=self.settings,
        )

    async def _create_notify_service(
        self,
        my_sql_connection_pool: Pool,
        mongo_db_connection: AsyncIOMotorDatabase,
        settings: Settings,
    ):
        if self._notify_service is None:
            self._notify_service = await NotifyService.create_service(
                my_sql_connection_pool=my_sql_connection_pool,
                mongo_db_connection=mongo_db_connection,
                static_dir_path=settings.STATIC_DIR,
                turbo_sms_config=settings.TURBO_SMS_CONFIG,
                sender=settings.SMS_SENDER,
                use_sso=settings.USE_SSO,
                bot_token=settings.TELEGRAM_BOT_TOKEN,
                billing_group_chat_id=settings.BILLING_MESSAGES_TELEGRAM_ID,
            )
        return self._notify_service

    async def _create_telegram_service(
        self,
        my_sql_connection_pool: Pool,
        mongo_db_connection: AsyncIOMotorDatabase,
        settings: Settings,
    ):
        if self._telegram_service is None:
            self._telegram_service = await TelegramService.create_service(
                my_sql_connection_pool=my_sql_connection_pool,
                mongo_db_connection=mongo_db_connection,
                static_dir_path=settings.STATIC_DIR,
            )
        return self._telegram_service


service_manager = ServiceManager()


async def init_telegram_bot_service_manager(
    settings: Settings,
    my_sql_connection_pool: Pool,
    mongo_db_connection: AsyncIOMotorDatabase,
):
    return await service_manager.create(
        settings=settings,
        my_sql_connection_pool=my_sql_connection_pool,
        mongo_db_connection=mongo_db_connection,
    )
