from fastapi import Query
from pydantic import BaseModel

from src.notify.adapters.models.user_billing import BillingGroup, BillingPacket
from src.notify.api.v1.schemas.base import BaseQuery


def validate_groups(
    group_ids: str | None = Query(None),
) -> list[str] | None:
    if group_ids is None:
        return None

    group_ids = group_ids.split(",")

    return group_ids


class QueryUserNotifySchema(BaseQuery):
    balance_gte: float | None = None
    balance_lte: float | None = None
    user_active: bool | None = None
    fee_more_than_balance: bool | None = None
    mac_equipment_delivered: bool | None = None
    sn_onu_equipment_delivered: bool | None = None


class BillingFiltersResponseSchema(BaseModel):
    groups: list[BillingGroup]
    packets: list[BillingPacket]
