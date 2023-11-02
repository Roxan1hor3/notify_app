from pydantic import BaseModel


class UserBilling(BaseModel):
    id: int
    ip: str
    fio: str
    fee: float
    comment: str
    balance: float
    packet_name: str
    phone_number: str
    grp_name: str
    grp_id: int
    sn_onu: str
    phone_number_time: int
    sn_onu_time: int
    mac_time: int
    mac: str


class UserBillingFilter(BaseModel):
    group_ids: list[int] | None = None
    balance_gte: float | None = None
    balance_lte: float | None = None
    user_active: bool | None = None
    fee_more_than_balance: bool | None = None
    mac_equipment_delivered: bool | None = None
    sn_onu_equipment_delivered: bool | None = None
