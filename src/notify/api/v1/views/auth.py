import uuid
from base64 import b64encode
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from starlette import status

from src.notify.adapters.models.user import User
from src.notify.adapters.services.user_service import UserService
from src.notify.api.dependencies.auth import authenticate_user
from src.notify.api.dependencies.services import get_user_service

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

UserService = Annotated[UserService, Depends(get_user_service)]


@auth_router.post(
    "/login",
    status_code=status.HTTP_200_OK,
)
async def login(
    response: Response, user_service: UserService, user: Annotated[User, Depends(authenticate_user)]
):
    session_uuid = uuid.uuid4()
    await user_service.login(user_uuid=user.uuid, session_uuid=session_uuid)
    response.set_cookie(key="session_uuid", value=b64encode(str(session_uuid).encode('utf-8')).decode('utf-8'), httponly=True)
    return {"username": user.username, "session_uuid": session_uuid, "uuid": user.uuid}


@auth_router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
async def logout(
    user_service: UserService, user: Annotated[User, Depends(authenticate_user)]
):
    await user_service.logout(user_uuid=user.uuid)
    return {"message": "Logout in successfully"}


@auth_router.get(
    "/profile",
    status_code=status.HTTP_200_OK,
)
async def current_user(user: Annotated[User, Depends(authenticate_user)]):
    return {"username": user.username}
