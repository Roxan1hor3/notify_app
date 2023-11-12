from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile
from starlette import status
from starlette.requests import Request
from starlette.responses import FileResponse

from src.notify.adapters.services.notify_service import NotifyService
from src.notify.adapters.services.user_service import UserService
from src.notify.api.dependencies.auth import authorization_user
from src.notify.api.dependencies.services import get_notify_service, get_user_service
from src.notify.api.v1.schemas.notify import NotifyListResponseSchema, NotifyQueryParams
from src.notify.api.v1.schemas.users_schemas import (
    BillingFiltersResponseSchema,
    QueryUserNotifySchema,
    validate_groups,
    validate_packets,
)

notifies_router = APIRouter(
    prefix="/notify",
    tags=["notify"],
    dependencies=[Depends(authorization_user)],
)

UserService = Annotated[UserService, Depends(get_user_service)]
NotifyService = Annotated[NotifyService, Depends(get_notify_service)]


@notifies_router.get(
    "/users_file/",
    response_description="Returns a user notify file 'user_notify.xlsx'",
    status_code=status.HTTP_200_OK,
)
async def get_user_list(
    request: Request,
    user_service: UserService,
    groups: None | list[str] = Depends(validate_groups),
    packets: None | list[str] = Depends(validate_packets),
    params: QueryUserNotifySchema = Depends(),
):
    user_notify_file = await user_service.get_user_notify_file(
        params=params,
        group_ids=groups,
        packet_ids=packets,
    )
    return FileResponse(
        user_notify_file,
        filename="user_notify.xlsx",
        media_type="application/vnd.ms-excel",
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
        filename=f"notify_report_file.xlsx",
        media_type="application/vnd.ms-excel",
    )


@notifies_router.get(
    "/notify_history/",
    response_model=NotifyListResponseSchema,
    status_code=status.HTTP_200_OK,
)
async def get_notify_list(
    request: Request,
    params: Annotated[NotifyQueryParams, Depends()],
    notify_service: NotifyService,
):
    count, notifies = await notify_service.get_notifies_list(params=params)
    return {"count": count, "results": notifies}


@notifies_router.get(
    "/notify_report_file/",
    status_code=status.HTTP_200_OK,
)
async def get_notify_list(
    request: Request,
    notify_uuid: UUID,
    notify_service: NotifyService,
):
    notify_report = await notify_service.get_notify_report(notify_uuid=notify_uuid)
    return FileResponse(
        notify_report,
        filename=f"notify_report_file.xlsx",
        media_type="application/vnd.ms-excel",
    )


@notifies_router.get(
    "/profile",
    status_code=status.HTTP_200_OK,
)
async def current_user(request: Request):
    return {"username": request.state.username}


@notifies_router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
)
async def logout(request: Request, user_service: UserService):
    await user_service.logout(user_uuid=request.state.user_uuid)
    return {"message": "Logout in successfully"}
