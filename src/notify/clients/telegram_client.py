import logging

from httpx import HTTPError, post

logger = logging.getLogger(__name__)


class TelegramClient:
    TELEGRAM_URL = "https://api.telegram.org/"

    def __init__(self, telegram_bot_token: str, use_sso: bool = False):
        self.telegram_bot_token = telegram_bot_token
        self.use_sso = use_sso

    async def send_message(self, chat_id: int, text: str) -> bool:
        # if not self.use_sso:
        #     return True
        try:
            post(
                self.TELEGRAM_URL + f"bot{self.telegram_bot_token}/sendMessage",
                params={"chat_id": chat_id, "text": text},
            )
        except HTTPError as e:
            logging.error(e)
            return False
        return True
