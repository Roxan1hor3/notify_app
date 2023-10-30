from typing import Annotated

from fastapi import APIRouter, Depends
from starlette import status
from starlette.responses import FileResponse

from src.notify.adapters.services.user_service import UserService
from src.notify.api.dependencies.services import get_user_service
from src.notify.api.v1.schemas.users_schemas import QueryUserNotifySchema

notifies_router = APIRouter(
    prefix="/notify",
    tags=["notify"],
)

UserService = Annotated[UserService, Depends(get_user_service)]


@notifies_router.get(
    "/user_notify_file/",
    response_description="Returns a user notify file 'user_notify.csv'",
    status_code=status.HTTP_200_OK,
)
async def get_user_list(
    user_service: UserService,
    params: QueryUserNotifySchema = Depends(),
):
    user_notify_file = await user_service.get_user_notify_file(params=params)
    return FileResponse(
        user_notify_file,
        filename="user_notify_file.csv",
        media_type="text/csv",
    )
