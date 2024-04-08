from pydantic import BaseModel


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
