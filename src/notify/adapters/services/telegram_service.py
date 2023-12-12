from aiomysql import Pool
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.notify.adapters.models.telegram_connection_request import (
    TelegramConnectionRequest,
)
from src.notify.adapters.models.telegram_repair_request import TelegramRepairRequest
from src.notify.adapters.models.telegram_user import TelegramUser
from src.notify.adapters.models.user_billing import (
    UserBillingFilter,
    UserBillingForTelegram,
)
from src.notify.adapters.repos.billing_messages_repo import MessagesBillingRepo
from src.notify.adapters.repos.message_repo import MessageRepo
from src.notify.adapters.repos.telegram_connection_request_repo import (
    TelegramConnectionRequestRepo,
)
from src.notify.adapters.repos.telegram_repair_request_repo import (
    TelegramRepairRequestRepo,
)
from src.notify.adapters.repos.telegram_user_repo import TelegramUsersRepo
from src.notify.adapters.repos.user_biilling_repo import UsersBillingRepo
from src.notify.adapters.services.base import BaseService


class TelegramService(BaseService):
    users_billing_repo: UsersBillingRepo
    message_repo: MessageRepo
    messages_billing_repo: MessagesBillingRepo
    telegram_users_repo: TelegramUsersRepo
    telegram_connection_request_repo: TelegramConnectionRequestRepo
    telegram_repair_request_repo: TelegramRepairRequestRepo

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
        self.telegram_users_repo = await TelegramUsersRepo.create_repo(
            mongo_db_connection
        )
        self.telegram_connection_request_repo = (
            await TelegramConnectionRequestRepo.create_repo(mongo_db_connection)
        )
        self.telegram_repair_request_repo = await TelegramRepairRequestRepo.create_repo(
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

    async def update_user_billing_and_personal_account_id(
        self, personal_account_id: int, billing_id: int, chat_id: int
    ):
        return (
            await self.telegram_users_repo.update_user_billing_and_personal_account_id(
                personal_account_id=personal_account_id,
                billing_id=billing_id,
                chat_id=chat_id,
            )
        )

    async def save_connection_request(
        self, chat_id: int, fio: str, address: str, phone_number: str
    ) -> TelegramConnectionRequest:
        return await self.telegram_connection_request_repo.save_connection_request(
            TelegramConnectionRequest(
                chat_id=chat_id,
                fio=fio,
                address=address,
                phone_number=phone_number,
            )
        )

    async def save_repair_request(
        self, chat_id: int, fio: str, address: str, phone_number: str, problem: str
    ) -> TelegramRepairRequest:
        return await self.telegram_repair_request_repo.save_repair_request(
            TelegramRepairRequest(
                chat_id=chat_id,
                fio=fio,
                address=address,
                phone_number=phone_number,
                problem=problem,
            )
        )
