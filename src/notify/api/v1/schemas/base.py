from pydantic import BaseModel, conint


class BaseQuery(BaseModel):
    limit: conint(gt=0, le=100) = 10
    offset: conint(ge=0) = 0
    ordering: str | None = None
