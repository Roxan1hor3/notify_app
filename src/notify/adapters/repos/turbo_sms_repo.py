from src.notify.adapters.repos.base import BaseRepository
from src.notify.clients.turmo_sms_client import TurboSMSClient
from src.notify.config import TurboSMSConfig


class TurboSMSRepo(BaseRepository):
    turbo_sms_client: TurboSMSClient

    def __init__(self, turbo_sms_config: TurboSMSConfig, sender: str, use_sso: bool):
        super().__init__()
        self.turbo_sms_client = TurboSMSClient(
            turbo_sms_config=turbo_sms_config, sender=sender, use_sso=use_sso
        )

    async def send_billing_user_sms(self, phonenumbers: list[str], text: str) -> bool:
        return await self.turbo_sms_client.send_sms(
            destination=",".join(phonenumbers), text=text
        )

    async def get_current_balance(self):
        return await self.turbo_sms_client.get_current_balance()
