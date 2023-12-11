from pydantic import BaseModel, field_validator


class MessageBilling(BaseModel):
    reason_id: int
    reason: str
    time: int
    id: int
    fio: str

    @field_validator("fio", "reason", mode="before")
    def encoding_fio(cls, value):
        try:
            decoded_data = value.decode("cp1251")
        except UnicodeDecodeError:
            decoded_data = "Coding Error"
        return decoded_data
