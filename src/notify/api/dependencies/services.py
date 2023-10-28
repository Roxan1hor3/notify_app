from fastapi import Depends


class ServiceManager:
    _user_service: UserService = None

    async def create(
        self,
        settings: Settings,
        db_connection: AsyncIOMotorDatabase,
    ) -> None:
        self._user_service = await self.create_user_service(
            settings=settings, db_connection=db_connection
        )

    async def create_user_service(
        self, settings: Settings, db_connection: AsyncIOMotorDatabase
    ) -> UserService:
        if self._user_service is None:
            self._user_service = await UserService.create_service(
                db_connection,
                settings.STATIC_DIR,
                settings.MERCHANT_INFO,
                settings.GOOGLE_SERVICE_ACCOUNT_INFO,
            )
        return self._user_service


service_manager = ServiceManager()


async def init_service_manager(
    settings: Settings,
    db_connection: AsyncIOMotorDatabase,
):
    return await service_manager.create(settings=settings, db_connection=db_connection)


async def get_user_service(
    db_connection: AsyncIOMotorDatabase = Depends(get_db_conn),
    settings: Settings = Depends(get_settings),
) -> UserService:
    return await service_manager.create_user_service(
        settings=settings, db_connection=db_connection
    )
