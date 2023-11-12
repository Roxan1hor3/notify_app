from abc import ABC
from typing import Any, Callable

from numpy import NaN
from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_core.core_schema import (
    CoreSchema,
    ValidatorFunctionWrapHandler,
    no_info_wrap_validator_function,
    str_schema,
)


class BaseArgs(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BaseMatchParams(BaseModel):
    model_config = ConfigDict(extra="forbid")


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


def nan_to_str(value: NaN, validator: ValidatorFunctionWrapHandler) -> str | None:
    if value is NaN:
        return ""
    value = validator(str(value))
    return value


class NaNToEmptyStr(str):
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: Callable[[Any], CoreSchema]
    ) -> CoreSchema:
        result = no_info_wrap_validator_function(
            nan_to_str,
            str_schema(),
        )
        return result
