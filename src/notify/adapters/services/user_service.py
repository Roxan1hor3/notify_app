import csv
import logging
from datetime import datetime, timedelta
from os import path
from typing import Self
from uuid import UUID

from aiomysql import Connection
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import ValidationError

from src.notify.adapters.models.user import TempUser, User
from src.notify.adapters.models.user_billing import UserBillingFilter
from src.notify.adapters.repos.user_biilling_repo import UsersBillingRepo
from src.notify.adapters.repos.user_repo import UsersRepo
from src.notify.adapters.services.base import BaseService, ServiceError
from src.notify.api.v1.schemas.users_schemas import QueryUserNotifySchema

logger = logging.getLogger(__name__)


class UserService(BaseService):
    users_billing_repo: UsersBillingRepo
    users_repo: UsersRepo
    static_dir_path: str
    user_notify_file: str
    USER_NOTIFY_FILE_FIELDS = (
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

    def __init__(self, static_dir_path):
        self.static_dir_path = static_dir_path
        self.user_notify_file = path.join(self.static_dir_path, "user_notify.csv")
        self.new_users_file = path.join(self.static_dir_path, "new_users.csv")

    @classmethod
    async def create_service(
        cls,
        mysql_db_connection: Connection,
        mongo_db_connection: AsyncIOMotorDatabase,
        static_dir_path,
    ):
        self = cls(static_dir_path=static_dir_path)

        self.users_billing_repo = await UsersBillingRepo.create_repo(
            mysql_db_connection
        )
        self.users_repo = await UsersRepo.create_repo(mongo_db_connection)

        return self

    async def get_user_notify_file(
        self,
        params: QueryUserNotifySchema,
        group_ids: list[int] = None,
        packet_ids: list[int] = None,
    ) -> str:
        _filter = UserBillingFilter(
            **params.model_dump(), group_ids=group_ids, packet_ids=packet_ids
        )
        limit = 1000
        count = await self.users_billing_repo.get_users_count(_filter=_filter)
        with open(self.user_notify_file, mode="w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.USER_NOTIFY_FILE_FIELDS)
            writer.writeheader()
            for offset in range(0, count, limit):
                users = await self.users_billing_repo.get_list(
                    _filter=_filter,
                    limit=limit,
                    offset=offset,
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
                            "Номер телефона": user.phone_number,
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
                        }
                    )
                    for user in users
                ]
        return self.user_notify_file

    async def retrieve(self, username: str) -> User:
        return await self.users_repo.retrieve(username=username)

    async def retrieve_bu_session_uuid(self, session_uuid: UUID) -> User:
        return await self.users_repo.retrieve_bu_session_uuid(session_uuid=session_uuid)

    async def login(self, user_uuid: UUID, session_uuid: UUID) -> UUID:
        await self.users_repo.login(
            user_uuid=user_uuid,
            session_uuid=session_uuid,
            expire_time=datetime.now() + timedelta(days=1),
            last_login_date=datetime.now(),
        )
        return session_uuid

    async def upload_new_users(self) -> None:
        """Imports data from the CSV file."""
        if not path.exists(self.new_users_file):
            raise ServiceError(message="new users file does not exist")
        with open(self.new_users_file, "r") as csv_file:
            validation_errors = []
            csv_reader = csv.DictReader(csv_file)

            for row in csv_reader:
                try:
                    csv_data = TempUser(**row)
                except ValidationError as e:
                    validation_errors.append(e)
                    continue

                try:
                    await self._import(csv_data)
                except ValidationError as e:
                    validation_errors.append(e)
                    continue
        if validation_errors:
            logger.error(
                "Some validation errors in csv file %s - %s",
                self.new_users_file,
                validation_errors,
            )
        logger.error("Successful upload 'new_users_file.csv'")

    async def _import(self, temp_user: TempUser) -> None:
        username_exists = await self.users_repo.check_field_value_exists(
            field="username", value=temp_user.username
        )
        password_exists = await self.users_repo.check_field_value_exists(
            field="password", value=temp_user.password
        )
        if username_exists is False and password_exists is False:
            await self._import_create(temp_user)
        elif username_exists is False and password_exists is True:
            raise ServiceError(f"not unique password user: {temp_user.model_dump()}")
        else:
            await self._import_update(temp_user)

    async def _import_update(self, temp_user: TempUser) -> None:
        await self.users_repo.update_password(
            username=temp_user.username, password=temp_user.password
        )

    async def _import_create(self, temp_user: TempUser) -> None:
        await self.users_repo.save_user(user=User(**temp_user.model_dump()))

    async def get_filters(self):
        groups = await self.users_billing_repo.get_groups_filters()
        packets = await self.users_billing_repo.get_packets_filters()
        return {"groups": groups, "packets": packets}

    async def logout(self, user_uuid) -> None:
        await self.users_repo.logout(
            user_uuid=user_uuid,
        )
