import asyncio

from src.notify.adapters.repos.base import BaseRepository
from src.notify.clients.telegram_client import TelegramClient


class TelegramNotifyRepo(BaseRepository):
    telegram_client: TelegramClient

    def __init__(self, bot_token: str, use_sso: bool):
        super().__init__()
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
