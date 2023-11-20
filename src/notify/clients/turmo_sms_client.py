import logging

import httpx
from zeep.cache import InMemoryCache
from zeep.client import AsyncClient
from zeep.client import Client as ZeepClient
from zeep.transports import AsyncTransport

from src.notify.config import TurboSMSConfig

logger = logging.getLogger(__name__)


class TurboSMSClient:
    _client: AsyncClient | None = None
    wsdl: str = ""
    login: str = ""
    password: str = ""

    def __init__(self, turbo_sms_config: TurboSMSConfig, sender: str, use_sso: bool):
        self.wsdl = turbo_sms_config.wsdl
        self.login = turbo_sms_config.login
        self.password = turbo_sms_config.password
        self.sender = sender
        self.use_sso = use_sso

    @property
    def client(self) -> ZeepClient:
        if self._client is None:
            async_client = httpx.AsyncClient()
            wsdl_client = httpx.Client()
            transport = AsyncTransport(
                cache=InMemoryCache(),
                timeout=5,
                client=async_client,
                wsdl_client=wsdl_client,
            )
            self._client = AsyncClient(self.wsdl, transport=transport)

        return self._client

    async def send_sms(self, destination: str, text: str) -> bool:
        ok = True
        if self.use_sso is False:
            return ok
        try:
            await self.client.service.Auth(login=self.login, password=self.password)
            res = await self.client.service.SendSMS(
                sender=self.sender, destination=destination, text=text
            )
            if "Сообщения успешно отправлены" not in res:
                logger.warning(
                    "TurboSMSService: Message sending error %s, %s", destination, text
                )
                ok = False
        except Exception:
            ok = False
            logger.exception(
                "TurboSMSService. Unexpected exception during SMS sending. Receiver: %s",
                destination,
            )
        return ok

    async def get_current_balance(self) -> float:
        # if self.use_sso is False:
        #     return 0
        try:
            await self.client.service.Auth(login=self.login, password=self.password)
            res = await self.client.service.GetCreditBalance()
        except Exception as e:
            logger.exception(
                "TurboSMSService. Unexpected exception during GetCreditBalance",
            )
            raise e
        return res
