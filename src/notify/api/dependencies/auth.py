import datetime
from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel
from starlette import status

from src.notify.adapters.models.user import User
from src.notify.adapters.repos.exceptions import RepoObjectNotFound
from src.notify.adapters.services.user_service import UserService
from src.notify.api.dependencies.services import get_user_service
from src.notify.config import Settings, get_settings

UserService = Annotated[UserService, Depends(get_user_service)]
invalid_credentials = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Invalid credentials",
    headers={"WWW-Authenticate": "Bearer"},
)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


def create_access_token(
    secret_key: str,
    algorithm: str,
    data: dict,
    expires_delta: datetime.timedelta | None = None,
):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret_key, algorithm=algorithm)
    return encoded_jwt


async def get_current_user(
    settings: Annotated[Settings, Depends(get_settings)],
    user_service: UserService,
    token: Annotated[str, Depends(oauth2_scheme)],
):
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise invalid_credentials
        token_data = TokenData(username=username)
    except JWTError:
        raise invalid_credentials
    try:
        user = await user_service.retrieve(token_data.username)
    except RepoObjectNotFound:
        raise invalid_credentials
    if user is None:
        raise invalid_credentials
    if user.expire_time is None or user.expire_time < datetime.datetime.now():
        raise invalid_credentials
    if user.is_active is False:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user


async def authorization_user(
    request: Request, current_user: Annotated[User, Depends(get_current_user)]
):
    request.state.user_uuid = current_user.uuid
    request.state.username = current_user.username
    return current_user
