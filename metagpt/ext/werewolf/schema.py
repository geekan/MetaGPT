from typing import Any

from pydantic import BaseModel, Field, field_validator

from metagpt.schema import Message
from metagpt.utils.common import any_to_str_set


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
