from typing import Any
import json
from pydantic import BaseModel, Field, field_validator

from metagpt.schema import Message
from metagpt.utils.common import any_to_str_set
from metagpt.configs.llm_config import LLMType

class RoleExperience(BaseModel):
    id: str = ""
    name: str = ""
    profile: str
    reflection: str
    instruction: str = ""
    response: str
    outcome: str = ""
    round_id: str = ""
    game_setup: str = ""
    version: str = ""

    def rag_key(self) -> str:
        """For search"""
        return self.reflection


class WwMessage(Message):
    # Werewolf Message
    restricted_to: set[str] = Field(default=set(), validate_default=True)

    @field_validator("restricted_to", mode="before")
    @classmethod
    def check_restricted_to(cls, restricted_to: Any):
        return any_to_str_set(restricted_to if restricted_to else set())

def wrapper_none_error(func):
    """Wrapper for ValueError"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            # the to_jsonable_python of pydantic will raise PydanticSerializationError
            # return None to call the custom JSONEncoder
            return None
    return wrapper


class WwJsonEncoder(json.JSONEncoder):
    def __init__(self, *, skipkeys=False, ensure_ascii=True,
            check_circular=True, allow_nan=True, sort_keys=False,
            indent=None, separators=None, default=None):
        super().__init__(skipkeys=skipkeys, ensure_ascii=ensure_ascii,
            check_circular=check_circular, allow_nan=allow_nan, sort_keys=sort_keys,
            indent=indent, separators=separators, default=default)
        if default is not None:
            self.default = wrapper_none_error(default)

        
    def _default(self, obj):
        if isinstance(obj, type):  # handle class
            return {
                "__type__": obj.__name__,
                "__module__": obj.__module__
            }
        return super().default(obj)
