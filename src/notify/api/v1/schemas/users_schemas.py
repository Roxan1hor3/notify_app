from fastapi import Query
from pydantic import BaseModel

from src.notify.adapters.models.user_billing import BillingGroup, BillingPacket


def validate_groups(
    groups: str | None = Query(None),
) -> list[str] | None:
    if groups is None:
        return None

    groups = groups.split(",")

    return groups


def validate_packets(
    packets: str | None = Query(None),
) -> list[str] | None:
    if packets is None:
        return None

    packets = packets.split(",")

    return packets


class QueryUserNotifySchema(BaseModel):
    balance_gte: float | None = None
    balance_lte: float | None = None
    user_active: bool | None = None
    fee_more_than_balance: bool | None = None
    mac_equipment_delivered: bool | None = None
    sn_onu_equipment_delivered: bool | None = None


class BillingFiltersResponseSchema(BaseModel):
    groups: list[BillingGroup]
    packets: list[BillingPacket]
