import csv
import logging
import uuid
from datetime import datetime
from os import path
from typing import Self

from aiomysql import Connection

from src.notify.adapters.models.user import UserFilter
from src.notify.adapters.repos.user_repo import UsersRepo
from src.notify.adapters.services.base import BaseService
from src.notify.api.v1.schemas.users_schemas import QueryUserNotifySchema

logger = logging.getLogger(__name__)


class UserService(BaseService):
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
        self.user_notify_file = path.join(self.static_dir_path, "user_notify")

    @classmethod
    async def create_service(
        cls,
        mysql_db_connection: Connection,
        static_dir_path,
    ) -> Self:
        self = cls(static_dir_path=static_dir_path)

        self.users_repo = await UsersRepo.create_repo(mysql_db_connection)

        return self

    async def get_user_notify_file(self, params: QueryUserNotifySchema, group_ids: list[int] = None) -> str:
        _filter = UserFilter(**params.model_dump(), group_ids=group_ids)
        limit = 1000
        count = await self.users_repo.get_users_count(_filter=_filter)
        new_user_notify_file_name = f"{self.user_notify_file}_{str(uuid.uuid4())}.csv"
        with open(new_user_notify_file_name, mode="w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.USER_NOTIFY_FILE_FIELDS)
            writer.writeheader()
            for offset in range(0, count, limit):
                count, users = await self.users_repo.get_list(
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
                            "Баланс": user.balance,
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
        return new_user_notify_file_name
