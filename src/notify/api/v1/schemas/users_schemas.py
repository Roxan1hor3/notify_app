from src.notify.api.v1.schemas.base import BaseQuery


class QueryUserNotifySchema(BaseQuery):
    group_ids: list[int] | None = None
    balance_gte: float | None = None
    balance_lte: float | None = None
    user_active: bool | None = None
    fee_more_than_balance: bool | None = None
    equipment_delivered: bool | None = None
