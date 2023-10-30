from aiomysql import Connection
from fastapi import Depends

from src.notify.adapters.services.user_service import UserService
from src.notify.api.dependencies.common import get_my_sql_db_conn
from src.notify.config import Settings, get_settings


class ServiceManager:
    _user_service: UserService = None

    async def create(
        self,
        settings: Settings,
        my_sql_connection: Connection,
    ) -> None:
        self._user_service = await self.create_user_service(
            settings=settings, my_sql_connection=my_sql_connection
        )

    async def create_user_service(
        self, my_sql_connection: Connection, settings: Settings
    ) -> UserService:
        if self._user_service is None:
            self._user_service = await UserService.create_service(
                my_sql_connection, settings.STATIC_DIR
            )
        return self._user_service


service_manager = ServiceManager()


async def init_service_manager(
    settings: Settings,
    my_sql_connection: Connection,
):
    return await service_manager.create(
        settings=settings, my_sql_connection=my_sql_connection
    )


async def get_user_service(
    my_sql_connection: Connection = Depends(get_my_sql_db_conn),
    settings: Settings = Depends(get_settings),
) -> UserService:
    return await service_manager.create_user_service(
        settings=settings, my_sql_connection=my_sql_connection
    )
