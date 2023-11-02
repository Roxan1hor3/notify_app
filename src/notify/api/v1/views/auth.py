import uuid
from typing import Annotated

from fastapi import APIRouter, Depends

from src.notify.adapters.models.user_billing import UserBilling
from src.notify.adapters.services.user_service import UserService
from src.notify.api.dependencies.auth import authenticate_user
from src.notify.api.dependencies.services import get_user_service

auth_router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

UserService = Annotated[UserService, Depends(get_user_service)]


@auth_router.post("/login")
async def login(
    user_service: UserService, user: Annotated[UserBilling, Depends(authenticate_user)]
):
    session_uuid = uuid.uuid4()
    await user_service.login(user_uuid=user.uuid, session_uuid=session_uuid)
    return {"message": "Logged in successfully", "session_uuid": session_uuid}
