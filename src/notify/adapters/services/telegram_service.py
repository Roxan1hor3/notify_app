from aiomysql import Pool
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.notify.adapters.models.telegram_user import TelegramUser
from src.notify.adapters.models.user_billing import (
    UserBillingFilter,
    UserBillingForTelegram,
)
from src.notify.adapters.repos.message_repo import MessageRepo
from src.notify.adapters.repos.telegram_user_repo import TelegramUsersRepo
from src.notify.adapters.repos.user_biilling_repo import UsersBillingRepo
from src.notify.adapters.services.base import BaseService


class TelegramService(BaseService):
    users_billing_repo: UsersBillingRepo
    message_repo: MessageRepo
    telegram_users_repo: TelegramUsersRepo

    def __init__(self, static_dir_path):
        self.static_dir_path = static_dir_path

    @classmethod
    async def create_service(
        cls,
        my_sql_connection_pool: Pool,
        mongo_db_connection: AsyncIOMotorDatabase,
        static_dir_path,
    ):
        self = cls(static_dir_path=static_dir_path)

        self.users_billing_repo = await UsersBillingRepo.create_repo(
            my_sql_connection_pool
        )
        # self.users_repo = await UsersRepo.create_repo(mongo_db_connection)
        self.telegram_users_repo = await TelegramUsersRepo.create_repo(
            mongo_db_connection
        )
        return self

    async def save_new_user(
        self,
        chat_id: int,
        first_name: str,
        last_name: str,
        username: str,
        personal_account_id: int | None = None,
        phone_number: str | None = None,
        billing_id: int | None = None,
    ) -> TelegramUser:
        return await self.telegram_users_repo.save_user(
            TelegramUser(
                chat_id=chat_id,
                first_name=first_name,
                last_name=last_name,
                username=username,
                personal_account_id=personal_account_id,
                phone_number=phone_number,
                billing_id=billing_id,
            )
        )

    async def retrieve_by_user_billing_id(
        self, billing_id: int
    ) -> None | UserBillingForTelegram:
        try:
            user = await self.users_billing_repo.retrieve(
                _filter=UserBillingFilter(uid=billing_id)
            )
        except Exception:
            return None
        return user

    async def get_user(self, chat_id: int) -> TelegramUser:
        try:
            user = await self.telegram_users_repo.retrieve(chat_id=chat_id)
        except Exception:
            return None
        return user
