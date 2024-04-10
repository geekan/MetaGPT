from pydantic import BaseModel, Field

from metagpt.schema import Message


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


class WwMessage(Message):
    # Werewolf Message
    restricted_to: set[str] = Field(default={}, validate_default=True)
