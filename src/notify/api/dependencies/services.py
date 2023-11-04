from typing import Annotated

from aiomysql import Connection
from fastapi import Depends
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.notify.adapters.services.notify_service import NotifyService
from src.notify.adapters.services.user_service import UserService
from src.notify.api.dependencies.common import get_mongo_conn, get_my_sql_db_conn
from src.notify.config import Settings, get_settings


class ServiceManager:
    _user_service: UserService = None
    _notify_service: NotifyService = None

    async def create(
        self,
        settings: Settings,
        my_sql_connection: Connection,
        mongo_db_connection: AsyncIOMotorDatabase,
    ) -> None:
        self._user_service = await self.create_user_service(
            settings=settings,
            my_sql_connection=my_sql_connection,
            mongo_db_connection=mongo_db_connection,
        )
        self._notify_service = await self.create_notify_service(
            settings=settings,
            my_sql_connection=my_sql_connection,
            mongo_db_connection=mongo_db_connection,
        )

    async def create_user_service(
        self,
        my_sql_connection: Connection,
        mongo_db_connection: AsyncIOMotorDatabase,
        settings: Settings,
    ) -> UserService:
        if self._user_service is None:
            self._user_service = await UserService.create_service(
                my_sql_connection, mongo_db_connection, settings.STATIC_DIR
            )
        return self._user_service

    async def create_notify_service(
        self,
        my_sql_connection: Connection,
        mongo_db_connection: AsyncIOMotorDatabase,
        settings: Settings,
    ):
        if self._notify_service is None:
            self._notify_service = await NotifyService.create_service(
                mysql_db_connection=my_sql_connection,
                mongo_db_connection=mongo_db_connection,
                static_dir_path=settings.STATIC_DIR,
                turbo_sms_config=settings.TURBO_SMS_CONFIG,
                sender=settings.SMS_SENDER,
                use_sso=settings.USE_SSO,
            )
        return self._notify_service


service_manager = ServiceManager()


async def init_service_manager(
    settings: Settings,
    my_sql_connection: Connection,
    mongo_db_connection: AsyncIOMotorDatabase,
):
    return await service_manager.create(
        settings=settings,
        my_sql_connection=my_sql_connection,
        mongo_db_connection=mongo_db_connection,
    )


MySqlConnection = Annotated[Connection, Depends(get_my_sql_db_conn)]
MongoConnection = Annotated[Connection, Depends(get_mongo_conn)]


async def get_user_service(
    mongo_db_connection: MongoConnection,
    my_sql_connection: MySqlConnection,
    settings: Settings = Depends(get_settings),
) -> UserService:
    return await service_manager.create_user_service(
        settings=settings,
        my_sql_connection=my_sql_connection,
        mongo_db_connection=mongo_db_connection,
    )


async def get_notify_service(
    mongo_db_connection: MongoConnection,
    my_sql_connection: MySqlConnection,
    settings: Settings = Depends(get_settings),
) -> NotifyService:
    return await service_manager.create_notify_service(
        settings=settings,
        my_sql_connection=my_sql_connection,
        mongo_db_connection=mongo_db_connection,
    )
