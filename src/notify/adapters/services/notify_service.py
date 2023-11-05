import csv
import logging
from csv import DictReader
from datetime import datetime
from io import StringIO
from os import path
from typing import Self
from uuid import UUID

import magic
from aiomysql import Connection
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError

from src.notify.adapters.models.message import Message, MessageStatus
from src.notify.adapters.models.notify import Notify
from src.notify.adapters.models.user_billing import UserBillingMessageData, UserBillingFilter
from src.notify.adapters.repos.message_repo import MessageRepo
from src.notify.adapters.repos.notify_repo import NotifyRepo
from src.notify.adapters.repos.turbo_sms_repo import TurboSMSRepo
from src.notify.adapters.repos.user_biilling_repo import UsersBillingRepo
from src.notify.adapters.services.base import BaseService, ServiceError
from src.notify.api.v1.schemas.notify import NotifyQueryParams
from src.notify.config import TurboSMSConfig

logger = logging.getLogger(__name__)


class NotifyService(BaseService):
    CSVMediaType = [
        "text/plain",
        "text/x-csv",
        "application/csv",
        "application/x-csv",
        "text/csv",
        "text/comma-separated-values",
        "text/x-comma-separated-values",
        "text/tab-separated-values",
    ]
    USER_NOTIFY_REPORT_FILE_FIELDS = (
        "Абонент ID",
        "Група",
        "IP",
        "Абонент",
        "Абоненська плата",
        "Баланс",
        "Пакет",
        "Коментарій",
        "Номер телефона",
        "Час обновлення телефона",
        "Сирійний номер ONU",
        "Час обновлення сирійного номера ONU",
        "MAC адрес",
        "Час обновлення MAC адреса",
    )

    turbo_sms_repo: TurboSMSRepo
    notify_repo: NotifyRepo
    message_repo: MessageRepo
    users_billing_repo: UsersBillingRepo

    def __init__(self, static_dir_path):
        self.static_dir_path = static_dir_path
        self.user_notify_report = path.join(
            self.static_dir_path, "user_notify_report.csv"
        )

    @classmethod
    async def create_service(
        cls,
        mysql_db_connection: Connection,
        mongo_db_connection: AsyncIOMotorDatabase,
        static_dir_path,
        turbo_sms_config: TurboSMSConfig,
        sender: str,
        use_sso: bool,
    ):
        self = cls(static_dir_path=static_dir_path)

        self.turbo_sms_repo = TurboSMSRepo(
            turbo_sms_config=turbo_sms_config, sender=sender, use_sso=use_sso
        )
        self.notify_repo = await NotifyRepo.create_repo(
            db_connection=mongo_db_connection
        )
        self.message_repo = await MessageRepo.create_repo(
            db_connection=mongo_db_connection
        )
        self.users_billing_repo = await UsersBillingRepo.create_repo(
            mysql_db_connection
        )

        return self

    async def validate_update_file(self, update_file: UploadFile) -> None:
        # 16 MB
        if update_file.size > 16 * 1024 * 1024:
            raise ServiceError(message="File too large.")
        lm = magic.Magic(mime=True, uncompress=False)
        await update_file.seek(0)
        content_type = lm.from_buffer(await update_file.read(2048))
        await update_file.seek(0)
        if content_type not in self.CSVMediaType:
            raise ServiceError(
                message=f"File must be in csv format. Yor format is {content_type}."
            )

    async def _get_csv_reader_from_update_file(
        self, update_file: UploadFile
    ) -> DictReader:
        await self.validate_update_file(update_file)
        return csv.DictReader(StringIO((await update_file.read()).decode("utf-8")))

    async def send_sms_by_file(
        self, sms_file: UploadFile, message_text: str, user_uuid, username
    ) -> str:
        csv_reader = await self._get_csv_reader_from_update_file(update_file=sms_file)
        if csv_reader.fieldnames is None:
            raise ServiceError(message="File must contain id and phone_number columns.")
        repeated_phone_numbers = []
        with open(self.user_notify_report, mode="w") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=[*csv_reader.fieldnames, "Статус відправки"]
            )
            writer.writeheader()
            user_billing_messages_data = []
            for row in csv_reader:
                try:
                    message = UserBillingMessageData(**row)
                except ValidationError:
                    raise ServiceError(
                        message="File must contain id and phone_number columns."
                    )
                if message.phone_number in repeated_phone_numbers:
                    message.status = MessageStatus.PHONE_NUMBER_IS_REPEATED
                repeated_phone_numbers.append(message.phone_number)

                user_billing_messages_data.append(message)
                writer.writerow({**row, "Статус відправки": message.status})
            try:
                async with self.notify_repo.start_transaction() as session:
                    notify = await self.notify_repo.save_notify(
                        notify=Notify(
                            message=message_text,
                            user_uuid=user_uuid,
                            username=username,
                        ),
                        session=session,
                    )
                    messages = await self.message_repo.bulk_save_messages(
                        messages=[
                            Message(
                                user_id=mes.id,
                                phone_number=mes.phone_number,
                                notify_uuid=notify.uuid,
                                status=mes.status,
                            )
                            for mes in user_billing_messages_data
                        ],
                        session=session,
                    )
                    res = await self.turbo_sms_repo.send_billing_user_sms(
                        phonenumbers=[
                            message.phone_number
                            for message in messages
                            if message.status == MessageStatus.SANDED
                        ],
                        text=message_text,
                    )
                    if res is not True:
                        raise ServiceError(message="Unexpected Error. Please try again.")
            except Exception as e:
                logger.error("Unexpected Error.")
                logger.error(str(e))
                raise ServiceError(message="Unexpected Error. Please try again.")
        await sms_file.close()
        return self.user_notify_report

    async def get_current_turbo_sms_balance(self):
        return await self.turbo_sms_repo.get_current_balance()

    async def get_notifies_list(self, params: NotifyQueryParams):
        count = await self.notify_repo.get_notify_count(username=params.username)
        results = await self.notify_repo.get_list(
            username=params.username,
            ordering=params.ordering,
            limit=params.limit,
            offset=params.offset,
        )
        return count, results

    async def get_notify_report(self, notify_uuid: UUID) -> str:
        limit = 1000
        messages = await self.message_repo.get_list(notify_uuid=notify_uuid)
        user_id_message_map = {message.user_id: message for message in messages}
        with open(self.user_notify_report, mode="w") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=[*self.USER_NOTIFY_REPORT_FILE_FIELDS, "Статус відправки"]
            )
            _filter = UserBillingFilter(_ids=user_id_message_map.values())
            count = await self.users_billing_repo.get_users_count(_filter=_filter)
            for offset in range(0, count, limit):
                users = await self.users_billing_repo.get_list(_filter=_filter, offset=offset, limit=limit)
                [
                    writer.writerow(
                        {
                            "Абонент ID": user.id,
                            "Група": user.grp_id,
                            "IP": user.ip,
                            "Абонент": user.fio,
                            "Абоненська плата": user.fee,
                            "Баланс": round(user.balance),
                            "Пакет": user.packet_name,
                            "Коментарій": user.comment,
                            "Номер телефона": user_id_message_map[user.id].phone_number,
                            "Час обновлення телефона": datetime.fromtimestamp(
                                user.phone_number_time
                            ),
                            "Сирійний номер ONU": user.sn_onu,
                            "Час обновлення сирійного номера ONU": datetime.fromtimestamp(
                                user.sn_onu_time
                            ),
                            "MAC адрес": user.mac,
                            "Час обновлення MAC адреса": datetime.fromtimestamp(
                                user.mac_time
                            ),
                            "Статус відправки": user_id_message_map[user.id].status
                        }
                    )
                    for user in users
                ]
        return self.user_notify_report

