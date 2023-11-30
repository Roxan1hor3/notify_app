import hashlib
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from starlette import status

from src.notify.adapters.repos.exceptions import RepoObjectNotFound
from src.notify.adapters.services.user_service import UserService
from src.notify.api.dependencies.auth import (
    Token,
    create_access_token,
    invalid_credentials,
)
from src.notify.api.dependencies.services import get_user_service
from src.notify.config import Settings, get_settings

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

UserService = Annotated[UserService, Depends(get_user_service)]


@auth_router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
)
async def login(
    user_service: UserService,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    settings: Settings = Depends(get_settings),
):
    try:
        user = await user_service.retrieve(username=form_data.username)
    except RepoObjectNotFound:
        raise invalid_credentials
    if user.password != hashlib.md5(form_data.password.encode()).hexdigest():
        raise invalid_credentials
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires,
        algorithm=settings.ALGORITHM,
        secret_key=settings.SECRET_KEY,
    )
    await user_service.login(user.username, access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}
