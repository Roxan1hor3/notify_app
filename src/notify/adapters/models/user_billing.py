from typing import Annotated

import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from pydantic import BaseModel, Field, model_validator

from src.notify.adapters.models.message import MessageStatus


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
    ids: list[int] | None = None
    group_ids: list[int] | None = None
    packet_ids: list[int] | None = None
    balance_gte: float | None = None
    balance_lte: float | None = None
    user_active: bool | None = None
    fee_more_than_balance: bool | None = None
    mac_equipment_delivered: bool | None = None
    sn_onu_equipment_delivered: bool | None = None
    fio: str | None = None
    is_auth: bool | None = None
    is_discount: bool | None = None


class BillingGroup(BaseModel):
    grp_name: str
    grp_id: int


class BillingPacket(BaseModel):
    name: str
    id: int


class UserBillingMessageData(BaseModel):
    id: Annotated[int, Field(alias="Абонент ID")]
    phone_number: Annotated[str, Field(alias="Номер телефона")]

    @model_validator(mode="after")
    def pre_save(self):
        try:
            phone = phonenumbers.parse(self.phone_number)
            if not phonenumbers.is_valid_number(phone):
                self.status = MessageStatus.NOT_VALID_PHONE_NUMBER
        except NumberParseException:
            self.status = MessageStatus.NOT_VALID_PHONE_NUMBER
        self.status = MessageStatus.SANDED
        return self
