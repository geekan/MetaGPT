from metagpt.environment.werewolf.const import RoleType
from metagpt.ext.werewolf.actions import Speak
from metagpt.ext.werewolf.roles import BasePlayer
from metagpt.ext.werewolf.schema import WwMessage
from metagpt.logs import logger


async def _act(self):
    todo = self.rc.todo

    memories = self.get_all_memories()

    input_instruction = f"""
    ## As a reminder, you have access to the following game history:
    {memories}
    ## You are {self.name}({self.profile})
    ## Guidance:
    1. If you are performing a special action or exercising a vote,
    end your response with "PlayerX", replace PlayerX with the actual player name, e.g., "..., kill/protect/poison/.../vote Player1".
    2. If it is a daytime free speech, you can speak in whatever format.
    Now, please speak:
    """
    rsp = input(input_instruction)  # wait for human input

    msg_cause_by = type(todo)
    msg_restricted_to = {} if isinstance(todo, Speak) else {RoleType.MODERATOR.value, self.profile}

    msg = WwMessage(
        content=rsp,
        role=self.profile,
        sent_from=self.name,
        cause_by=msg_cause_by,
        send_to={},
        restricted_to=msg_restricted_to,  # 给Moderator及自身阵营发送加密消息
    )

    logger.info(f"{self._setting}: {rsp}")

    return msg


def prepare_human_player(player_class: BasePlayer):
    # Dynamically define a human player class that inherits from a certain role class
    HumanPlayer = type("HumanPlayer", (player_class,), {"_act": _act})
    return HumanPlayer
