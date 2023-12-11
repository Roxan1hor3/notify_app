from src.notify.adapters.models.telegram_user import TelegramUser
from src.notify.adapters.queries.telegram_user_query import TelegramUserQuery
from src.notify.adapters.repos.base import BaseMotorRepo


class TelegramUsersRepo(BaseMotorRepo):
    MODEL = TelegramUser
    query_storage = TelegramUserQuery()

    async def init_indexes(self):
        await self.collection.create_index([("chat_id", 1)], unique=True)
        await self.collection.create_index([("personal_account_id", 1)])
        await self.collection.create_index([("phone_number", 1)])

    async def save_user(self, telegram_user: TelegramUser) -> TelegramUser:
        await self.collection.replace_one(
            filter={"chat_id": telegram_user.chat_id},
            replacement=telegram_user.model_dump(),
            upsert=True,
        )
        return telegram_user

    async def retrieve(self, chat_id: int) -> TelegramUser:
        user = await self.collection.find_one({"chat_id": chat_id})
        return TelegramUser(**user)

    async def get_list(
        self, phone_numbers: list[str], billing_ids: list[int]
    ) -> list[TelegramUser]:
        results = await self.collection.find(
            {
                "$or": [
                    {"billing_id": {"$in": billing_ids}},
                    {"phone_number": {"$in": phone_numbers}},
                ]
            }
        ).to_list(length=None)
        return [TelegramUser(**user) for user in results]

    async def send_message_billing_in_telegram_group(self, message):
        pass
