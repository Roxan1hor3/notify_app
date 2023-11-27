import logging
from datetime import datetime
from os import path
from uuid import UUID

import magic
import xlsxwriter
from aiomysql import Pool
from fastapi import UploadFile
from motor.motor_asyncio import AsyncIOMotorDatabase
from pandas import DataFrame, ExcelWriter, notnull, read_excel
from pydantic import ValidationError

from src.notify.adapters.models.message import Message, MessageStatus
from src.notify.adapters.models.notify import Notify
from src.notify.adapters.models.user_billing import (
    UserBillingFilter,
    UserBillingMessageData,
)
from src.notify.adapters.repos.message_repo import MessageRepo
from src.notify.adapters.repos.notify_repo import NotifyRepo
from src.notify.adapters.repos.turbo_sms_repo import TurboSMSRepo
from src.notify.adapters.repos.user_biilling_repo import UsersBillingRepo
from src.notify.adapters.services.base import BaseService, ServiceError
from src.notify.api.v1.schemas.notify import NotifyQueryParams
from src.notify.config import TurboSMSConfig

logger = logging.getLogger(__name__)


class NotifyService(BaseService):
    EXCELMediaType = [
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
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
            self.static_dir_path, "user_notify_report.xlsx"
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

        return self

    async def validate_update_file(self, update_file: UploadFile) -> None:
        # 16 MB
        if update_file.size > 16 * 1024 * 1024:
            raise ServiceError(message="File too large.")
        lm = magic.Magic(mime=True, uncompress=False)
        await update_file.seek(0)
        content_type = lm.from_buffer(await update_file.read(2048))
        await update_file.seek(0)
        if content_type not in self.EXCELMediaType:
            raise ServiceError(
                message=f"File must be in excel format. Yor format is {content_type}."
            )

    async def _get_excel_data_df_from_update_file(
        self, update_file: UploadFile
    ) -> DataFrame:
        await self.validate_update_file(update_file)
        return read_excel(await update_file.read())

    async def send_sms_by_file(
        self, sms_file: UploadFile, message_text: str, user_uuid, username
    ) -> str:
        excel_data_df = await self._get_excel_data_df_from_update_file(
            update_file=sms_file
        )
        excel_data_df.where(notnull(excel_data_df), None)
        if not excel_data_df.columns.tolist():
            raise ServiceError(message="File must contain id and phone_number columns.")
        data_dict = excel_data_df.to_dict("records")
        repeated_phone_numbers = []
        user_billing_messages_data = []
        report_data = []
        for row in data_dict:
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
            report_data.append({**row, "Статус відправки": message.status})
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
        writer = ExcelWriter(self.user_notify_report, engine="xlsxwriter")
        if report_data:
            df = DataFrame.from_records(data=report_data)
            df.to_excel(
                writer,
                index=False,
                header=[*excel_data_df.columns.tolist(), "Статус відправки"],
                index_label="ID",
            )
        else:
            df = DataFrame(
                columns=[*excel_data_df.columns.tolist(), "Статус відправки"]
            )
            df.to_excel(
                writer,
                index=False,
                index_label=False,
                header=True,
            )
        worksheet = writer.sheets["Sheet1"]
        worksheet.autofit()
        writer.close()
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
        workbook = xlsxwriter.Workbook(self.user_notify_report)
        worksheet = workbook.add_worksheet()
        headers = [*self.USER_NOTIFY_REPORT_FILE_FIELDS, "Статус відправки"]
        for col_num, header in enumerate(headers):
            worksheet.write(0, col_num, header)
        _filter = UserBillingFilter(ids=list(user_id_message_map.keys()))
        count = await self.users_billing_repo.get_users_count(_filter=_filter)
        row = 1
        for offset in range(0, count, limit):
            users = await self.users_billing_repo.get_list(
                _filter=_filter, offset=offset, limit=limit
            )
            for user in users:
                worksheet.write(row, 0, user.id)
                worksheet.write(row, 1, user.grp_name)
                worksheet.write(row, 2, user.ip)
                worksheet.write(row, 3, user.fio)
                worksheet.write(row, 4, user.fee)
                worksheet.write(row, 5, round(user.balance))
                worksheet.write(row, 6, user.packet_name)
                worksheet.write(row, 7, user.comment)
                phone_number = (
                    user_id_message_map[user.id].phone_number
                    if user_id_message_map.get(user.id) is not None
                    else ""
                )
                worksheet.write(row, 8, phone_number)
                worksheet.write(
                    row,
                    9,
                    datetime.fromtimestamp(user.phone_number_time).strftime(
                        "%Y-%m-%d %H:%M"
                    ),
                )
                worksheet.write(row, 10, user.sn_onu)
                worksheet.write(
                    row,
                    11,
                    datetime.fromtimestamp(user.sn_onu_time).strftime("%Y-%m-%d %H:%M"),
                )
                worksheet.write(row, 12, user.mac)
                worksheet.write(
                    row,
                    13,
                    datetime.fromtimestamp(user.mac_time).strftime("%Y-%m-%d %H:%M"),
                )
                status = (
                    user_id_message_map[user.id].status
                    if user_id_message_map.get(user.id) is not None
                    else ""
                )
                worksheet.write(row, 14, status)

                row += 1
        worksheet.autofit()
        workbook.close()
        return self.user_notify_report
