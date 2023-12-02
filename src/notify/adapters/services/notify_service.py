import csv
import logging
from csv import DictReader
from datetime import datetime
from io import StringIO
from os import path
from uuid import UUID

import magic
from aiomysql import Pool
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError

from src.notify.adapters.models.message import Message, MessageStatus
from src.notify.adapters.models.notify import Notify, NotifyServices
from src.notify.adapters.models.user_billing import (
    UserBillingFilter,
    UserBillingMessageData,
)
from src.notify.adapters.repos.message_repo import MessageRepo
from src.notify.adapters.repos.notify_repo import NotifyRepo
from src.notify.adapters.repos.telegram_notify_repo import TelegramNotifyRepo
from src.notify.adapters.repos.telegram_user_repo import TelegramUsersRepo
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
    telegram_users_repo: TelegramUsersRepo
    telegram_notify_repo: TelegramNotifyRepo

    def __init__(self, static_dir_path):
        self.static_dir_path = static_dir_path
        self.user_notify_report = path.join(
            self.static_dir_path, "user_notify_report.csv"
        )

    @classmethod
    async def create_service(
        cls,
        my_sql_connection_pool: Pool,
        mongo_db_connection: AsyncIOMotorDatabase,
        static_dir_path,
        turbo_sms_config: TurboSMSConfig,
        sender: str,
        use_sso: bool,
        bot_token: str,
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
            my_sql_connection_pool
        )
        self.telegram_users_repo = await TelegramUsersRepo.create_repo(
            mongo_db_connection
        )
        self.telegram_notify_repo = TelegramNotifyRepo(
            use_sso=use_sso, bot_token=bot_token
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
                        sent_by=NotifyServices.SMS,
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

    async def send_telegram_notify_by_file(
        self, telegram_notify_file: UploadFile, message_text: str, user_uuid, username
    ):
        csv_reader = await self._get_csv_reader_from_update_file(
            update_file=telegram_notify_file
        )
        if csv_reader.fieldnames is None:
            raise ServiceError(message="File must contain id and phone_number columns.")
        user_billing_messages_data = []
        valid_phone_numbers = []
        user_billing_ids = []
        list_csv_reader = list(csv_reader)
        for row in list_csv_reader:
            try:
                message = UserBillingMessageData(**row)
            except ValidationError:
                raise ServiceError(
                    message="File must contain id and phone_number columns."
                )
            user_billing_messages_data.append(message)
            valid_phone_numbers.append(
                message.phone_number
                if message.phone_number.startswith("+380")
                else "+380" + message.phone_number
            )
            user_billing_ids.append(message.id)
        telegram_users = await self.telegram_users_repo.get_list(
            phone_numbers=valid_phone_numbers, billing_ids=user_billing_ids
        )
        map_billing_id_to_chat_id = {
            user.billing_id: user.chat_id for user in telegram_users
        }
        try:
            async with self.notify_repo.start_transaction() as session:
                notify = await self.notify_repo.save_notify(
                    notify=Notify(
                        message=message_text,
                        user_uuid=user_uuid,
                        username=username,
                        sent_by=NotifyServices.TELEGRAM,
                    ),
                    session=session,
                )
                messages = await self.message_repo.bulk_save_messages(
                    messages=[
                        Message(
                            user_id=mes.id,
                            phone_number=mes.phone_number,
                            notify_uuid=notify.uuid,
                            telegram_chat_id=map_billing_id_to_chat_id.get(mes.id),
                            status=MessageStatus.SANDED
                            if mes.id in map_billing_id_to_chat_id.keys()
                            else MessageStatus.NOT_REGISTERED_TELEGRAM,
                        )
                        for mes in user_billing_messages_data
                    ],
                    session=session,
                )
                res = await self.telegram_notify_repo.send_telegram_users_messages(
                    chat_ids=[
                        message.telegram_chat_id
                        for message in messages
                        if message.status == MessageStatus.SANDED
                        and message.telegram_chat_id is not None
                    ],
                    text=message_text,
                )
                if res is not True:
                    raise ServiceError(message="Unexpected Error. Please try again.")
        except Exception as e:
            logger.error("Unexpected Error.")
            logger.error(str(e))
            raise ServiceError(message="Unexpected Error. Please try again.")
        with open(self.user_notify_report, mode="w") as csvfile:
            writer = csv.DictWriter(
                csvfile, fieldnames=[*csv_reader.fieldnames, "Статус відправки"]
            )
            writer.writeheader()
            for row in list_csv_reader:
                if row.get("id") in map_billing_id_to_chat_id.keys():
                    writer.writerow({**row, "Статус відправки": MessageStatus.SANDED})
                else:
                    writer.writerow(
                        {
                            **row,
                            "Статус відправки": MessageStatus.NOT_REGISTERED_TELEGRAM,
                        }
                    )
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
                csvfile,
                fieldnames=[*self.USER_NOTIFY_REPORT_FILE_FIELDS, "Статус відправки"],
            )
            _filter = UserBillingFilter(ids=list(user_id_message_map.keys()))
            count = await self.users_billing_repo.get_users_count(_filter=_filter)
            for offset in range(0, count, limit):
                users = await self.users_billing_repo.get_list(
                    _filter=_filter, offset=offset, limit=limit
                )
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
                            "Номер телефона": user_id_message_map[user.id].phone_number
                            if user_id_message_map.get(user.id) is not None
                            else "",
                            "Час обновлення телефона": datetime.fromtimestamp(
                                user.phone_number_time
                            ).strftime("%Y-%m-%d %H:%M"),
                            "Сирійний номер ONU": user.sn_onu,
                            "Час обновлення сирійного номера ONU": datetime.fromtimestamp(
                                user.sn_onu_time
                            ).strftime(
                                "%Y-%m-%d %H:%M"
                            ),
                            "MAC адрес": user.mac,
                            "Час обновлення MAC адреса": datetime.fromtimestamp(
                                user.mac_time
                            ).strftime("%Y-%m-%d %H:%M"),
                            "Статус відправки": user_id_message_map[user.id].status
                            if user_id_message_map.get(user.id) is not None
                            else "",
                        }
                    )
                    for user in users
                ]
        return self.user_notify_report
