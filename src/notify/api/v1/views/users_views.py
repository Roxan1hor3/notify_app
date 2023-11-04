from typing import Annotated

from fastapi import APIRouter, Depends, File, UploadFile
from starlette import status
from starlette.requests import Request
from starlette.responses import FileResponse

from src.notify.adapters.services.notify_service import NotifyService
from src.notify.adapters.services.user_service import UserService
from src.notify.api.dependencies.auth import get_authenticated_user_from_session_id
from src.notify.api.dependencies.services import get_notify_service, get_user_service
from src.notify.api.v1.schemas.users_schemas import (
    BillingFiltersResponseSchema,
    QueryUserNotifySchema,
    validate_groups,
)

notifies_router = APIRouter(
    prefix="/notify",
    tags=["notify"],
    dependencies=[Depends(get_authenticated_user_from_session_id)],
)

UserService = Annotated[UserService, Depends(get_user_service)]
NotifyService = Annotated[NotifyService, Depends(get_notify_service)]


@notifies_router.get(
    "/users_file/",
    response_description="Returns a user notify file 'user_notify.csv'",
    status_code=status.HTTP_200_OK,
)
async def get_user_list(
    request: Request,
    user_service: UserService,
    group_ids: None | list[str] = Depends(validate_groups),
    params: QueryUserNotifySchema = Depends(),
):
    user_notify_file = await user_service.get_user_notify_file(
        params=params, group_ids=group_ids
    )
    return FileResponse(
        user_notify_file,
        filename="user_notify_file.csv",
        media_type="text/csv",
    )


@notifies_router.get(
    "/filters/",
    response_model=BillingFiltersResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_user_list(
    request: Request,
    user_service: UserService,
):
    _filters = await user_service.get_filters()
    return _filters


@notifies_router.get(
    "/current_balance/",
    status_code=status.HTTP_200_OK,
)
async def get_user_list(
    request: Request,
    notify_service: NotifyService,
):
    current_balance = await notify_service.get_current_turbo_sms_balance()
    return {"current_balance": current_balance}


@notifies_router.post(
    "/send_sms_by_file/",
    status_code=status.HTTP_200_OK,
)
async def get_user_list(
    request: Request,
    notify_service: NotifyService,
    message: str,
    sms_file: Annotated[UploadFile, File(alias="sms_file")],
):
    notify_report_file = await notify_service.send_sms_by_file(
        sms_file=sms_file,
        message_text=message,
        user_uuid=request.state.user_uuid,
        username=request.state.username,
    )
    return FileResponse(
        notify_report_file,
        filename=f"notify_report_file.csv",
        media_type="text/csv",
    )
