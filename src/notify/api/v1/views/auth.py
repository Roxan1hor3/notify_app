import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
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
    user_service: UserService, user: Annotated[User, Depends(authenticate_user)]
):
    session_uuid = uuid.uuid4()
    await user_service.login(user_uuid=user.uuid, session_uuid=session_uuid)
    return {"message": "Logged in successfully", "session_uuid": session_uuid}


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
    "/current_user",
    status_code=status.HTTP_200_OK,
)
async def current_user(user: Annotated[User, Depends(authenticate_user)]):
    return {"username": user.username}
