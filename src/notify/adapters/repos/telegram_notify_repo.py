import asyncio
from datetime import datetime

from src.notify.adapters.models.message_billing import MessageBilling
from src.notify.adapters.repos.base import BaseRepository
from src.notify.clients.telegram_client import TelegramClient


class TelegramNotifyRepo(BaseRepository):
    telegram_client: TelegramClient
    billing_group_chat_id: int

    def __init__(self, bot_token: str, use_sso: bool, billing_group_chat_id: int):
        super().__init__()
        self.billing_group_chat_id = billing_group_chat_id
        self.telegram_client = TelegramClient(
            telegram_bot_token=bot_token, use_sso=use_sso
        )

    async def send_telegram_users_messages(
        self, chat_ids: list[int], text: str
    ) -> bool:
        results = await asyncio.gather(
            *[
                self.telegram_client.send_message(chat_id=chat_id, text=text)
                for chat_id in chat_ids
            ]
        )
        return all(results)

    async def send_message_billing_in_telegram_group(self, message: MessageBilling):
        await self.telegram_client.send_message(
            chat_id=self.billing_group_chat_id,
            text=f"Повідомлення в білінг від {message.fio}, id: {message.id}.\n"
            f"Текст повідомлення: {message.reason}\n"
            f"Час повідомлення: {datetime.fromtimestamp(message.time).strftime('%Y.%m.%d %H:%M')}.",
        )
