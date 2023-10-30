import csv
import logging
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
        "Абоненська плата активна",
        "Абоненська плата",
        "Баланс",
        "Пакет",
        "Номер телефона",
        "Коментарій",
        "Чи здав обладнання",
    )

    def __init__(self, static_dir_path):
        self.static_dir_path = static_dir_path
        self.user_notify_file = path.join(self.static_dir_path, "update_cl_report.csv")

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
            writer = csv.DictWriter(
                csvfile, fieldnames=self.OFFER_FB_UPDATE_FILE_FIELDS
            )
            for offset in range(0, count, limit):
                users = await self.users_repo.get_list(
                    _filter=_filter,
                    limit=limit,
                    offset=offset,
                    ordering=params.ordering,
                )
                [
                    writer.writerow(
                        {
                            "Абонент ID": None,
                            "Група": None,
                            "IP": None,
                            "Абонент": None,
                            "Абоненська плата активна": None,
                            "Абоненська плата": None,
                            "Баланс": None,
                            "Пакет": None,
                            "Номер телефона": None,
                            "Коментарій": None,
                            "Чи здав обладнання": None,
                        }
                    )
                    for user in users
                ]
        return self.user_notify_file
