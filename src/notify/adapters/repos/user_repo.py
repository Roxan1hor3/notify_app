from datetime import datetime
from typing import Any
from uuid import UUID

from src.notify.adapters.models.user import User
from src.notify.adapters.queries.user_query import UserQueryStorage
from src.notify.adapters.repos.base import BaseMotorRepo
from src.notify.adapters.repos.exceptions import RepoObjectNotFound


class UsersRepo(BaseMotorRepo):
    MODEL = User
    query_storage = UserQueryStorage()

    async def init_indexes(self):
        await self.collection.create_index([("uuid", 1)], unique=True)
        await self.collection.create_index([("session_uuid", 1)], unique=True)
        await self.collection.create_index([("password", 1)], unique=True)
        await self.collection.create_index([("username", 1)], unique=True)

    async def retrieve(self, username: str) -> User:
        doc = await self.collection.find_one({"username": username})
        if not doc:
            raise RepoObjectNotFound(message="User not found")
        return self.MODEL(**doc)

    async def retrieve_bu_session_uuid(self, session_uuid: UUID):
        doc = await self.collection.find_one({"session_uuid": session_uuid})
        if not doc:
            raise RepoObjectNotFound(message="User not found")
        return self.MODEL(**doc)

    async def login(
        self,
        user_uuid: UUID,
        session_uuid: UUID,
        expire_time: datetime,
        last_login_date: datetime,
    ):
        await self.collection.update_one(
            {"uuid": user_uuid},
            {
                "$set": {
                    "session_uuid": session_uuid,
                    "expire_time": expire_time,
                    "last_login_date": last_login_date,
                }
            },
        )

    async def check_field_value_exists(self, field: str, value: Any) -> bool:
        doc = await self.collection.find_one({field: value}, projection={"_id"})
        return bool(doc)

    async def update_password(self, username: str, password: str):
        await self.collection.update_one(
            {"username": username}, {"$set": {"password": password}}
        )

    async def save_user(self, user: User) -> None:
        await self.collection.insert_one(user.model_dump())

    async def logout(self, user_uuid: UUID) -> None:
        await self.collection.update_one(
            {"user_uuid": user_uuid},
            {
                "$set": {
                    "session_uuid": None,
                    "expire_time": None,
                }
            },
        )
