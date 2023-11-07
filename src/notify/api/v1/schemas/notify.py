from pydantic import BaseModel

from src.notify.adapters.models.notify import Notify
from src.notify.api.v1.schemas.base import BaseQuery


class NotifyListResponseSchema(BaseModel):
    results: list[Notify]
    count: int


class NotifyQueryParams(BaseQuery):
    username: str | None = None
    ordering: str = "-notify_date"
