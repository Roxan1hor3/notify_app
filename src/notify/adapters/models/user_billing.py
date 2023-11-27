from builtins import UnicodeDecodeError
from typing import Annotated

import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
from pydantic import BaseModel, Field, field_validator, model_validator

from src.notify.adapters.models.base import NaNToEmptyStr
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

    @field_validator(
        "fio", "packet_name", "comment", "grp_name", "phone_number", mode="before"
    )
    def encoding_fio(cls, value):
        try:
            decoded_data = value.decode("cp1251")
        except UnicodeDecodeError:
            decoded_data = "Coding Error"
        return decoded_data


class UserBillingForTelegram(BaseModel):
    id: int
    fee: float
    balance: float


class UserBillingFilter(BaseModel):
    uid: int | None = None
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

    @field_validator("grp_name", mode="before")
    def encoding_fio(cls, value):
        try:
            decoded_data = value.decode("cp1251")
        except UnicodeDecodeError:
            decoded_data = "Coding Error"
        return decoded_data


class BillingPacket(BaseModel):
    name: str
    id: int

    @field_validator("name", mode="before")
    def encoding_fio(cls, value):
        try:
            decoded_data = value.decode("cp1251")
        except UnicodeDecodeError:
            decoded_data = "Coding Error"
        return decoded_data


class UserBillingMessageData(BaseModel):
    id: Annotated[int, Field(alias="Абонент ID")]
    phone_number: Annotated[NaNToEmptyStr, Field(alias="Номер телефона")]
    status: MessageStatus | None = None

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
