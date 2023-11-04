from fastapi import APIRouter

from backend.src.notify.api.v1.views.auth import auth_router
from backend.src.notify.api.v1.views.users_views import notifies_router

v1_router = APIRouter(prefix="/v1", responses={404: {"description": "Not found"}})

v1_router.include_router(notifies_router)
v1_router.include_router(auth_router)
