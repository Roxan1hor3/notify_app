import base64
import datetime
import hashlib
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette import status
from starlette.requests import Request

from src.notify.adapters.repos.exceptions import RepoObjectNotFound
from src.notify.adapters.services.user_service import UserService
from src.notify.api.dependencies.services import get_user_service

UserService = Annotated[UserService, Depends(get_user_service)]
invalid_credentials = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Basic"},
)
invalid_session_uuid = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid session UUID",
)
session_uuid_expired = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Session UUID expired",
)

security = HTTPBasic()


async def authenticate_user(
    user_service: UserService,
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
):
    try:
        user = await user_service.retrieve(username=credentials.username)
    except RepoObjectNotFound:
        raise invalid_credentials
    if user.password != hashlib.md5(credentials.password.encode()).hexdigest():
        raise invalid_credentials
    return user


async def get_authenticated_user_from_session_id(
    user_service: UserService, request: Request
):
    session_uuid = request.cookies.get("session_uuid")
    if session_uuid is None:
        raise invalid_session_uuid
    try:
        user = await user_service.retrieve_bu_session_uuid(
            session_uuid=UUID(
                base64.b64decode(session_uuid.encode("utf-8")).decode("utf-8")
            )
        )
    except RepoObjectNotFound:
        raise invalid_credentials
    if user.expire_time is None or user.expire_time < datetime.datetime.now():
        raise session_uuid_expired
    request.state.user_uuid = user.uuid
    request.state.username = user.username
    return request
