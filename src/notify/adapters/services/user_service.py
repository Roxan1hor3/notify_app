import csv
import logging
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
        # "Абоненська плата активна",
        "Абоненська плата",
        "Баланс",
        "Пакет",
        "Номер телефона",
        "Коментарій",
        "Чи здав обладнання",
        "Час обновлення телефона",
        "Час обновлення обладнення",
    )

    def __init__(self, static_dir_path):
        self.static_dir_path = static_dir_path
        self.user_notify_file = path.join(self.static_dir_path, "user_notify.csv")

    @classmethod
    async def create_service(
        cls,
        mysql_db_connection: Connection,
        static_dir_path,
    ) -> Self:
        self = cls(static_dir_path=static_dir_path)

        self.users_repo = await UsersRepo.create_repo(mysql_db_connection)

        return self

    async def get_user_notify_file(self, params: QueryUserNotifySchema) -> str:
        _filter = UserFilter(**params.model_dump())
        limit = 1000
        count = await self.users_repo.get_users_count(_filter=_filter)
        with open(self.user_notify_file, mode="w") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.USER_NOTIFY_FILE_FIELDS)
            writer.writeheader()
            for offset in range(0, count, limit):
                count, users = await self.users_repo.get_list(
                    _filter=_filter,
                    limit=limit,
                    offset=offset,
                    ordering=params.ordering,
                )
                [
                    writer.writerow(
                        {
                            "Абонент ID": user.id,
                            "Група": user.grp_id,
                            "IP": user.ip,
                            "Абонент": user.fio,
                            # "Абоненська плата активна": user.,
                            "Абоненська плата": user.fee,
                            "Баланс": user.balance,
                            "Пакет": user.packet_name,
                            "Номер телефона": user.phone_number,
                            "Коментарій": user.comment,
                            "Чи здав обладнання": user.sn_onu,
                            "Час обновлення телефона": datetime.fromtimestamp(
                                user.phone_number_time
                            ),
                            "Час обновлення обладнення": datetime.fromtimestamp(
                                user.sn_onu_time
                            ),
                        }
                    )
                    for user in users
                ]
        return self.user_notify_file
