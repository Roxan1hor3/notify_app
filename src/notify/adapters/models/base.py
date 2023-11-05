from abc import ABC
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class BaseArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BaseMatchParams(BaseModel):
    model_config = ConfigDict(extra="forbid")

class StrEnum(str, Enum):
    pass


class RetrieveManyArgs(BaseArgs):
    ordering: str | None = None
    offset: int
    limit: int
    match_params: Any = None

    @field_validator("match_params", mode="after")
    def validate_match_params(cls, val):
        if issubclass(type(val), BaseMatchParams) or val is None:
            return val

        raise TypeError(
            "Wrong type for 'match_params', must be subclass of BaseMatchParams"
        )


class BaseEntityModel(ABC, BaseModel):
    """The base model for all DB entities"""

    __pk__ = ["uuid"]

    @staticmethod
    def get_entity_name():
        raise NotImplementedError
