from examples.werewolf_game.actions.seer_actions import Verify
from examples.werewolf_game.roles.base_player import BasePlayer
from examples.werewolf_game.actions import Speak
from metagpt.schema import Message
from metagpt.logs import logger


class Seer(BasePlayer):
    def __init__(
            self,
            name: str = "",
            profile: str = "Seer",
            special_action_names: list[str] = ["Verify"],
            **kwargs,
    ):
        super().__init__(name, profile, special_action_names, **kwargs)

    async def _act(self):
        todo = self._rc.todo
        logger.info(f"{self._setting}: ready to {str(todo)}")

        # 可以用这个函数获取该角色的全部记忆和最新的instruction
        memories = self.get_all_memories()
        latest_instruction = self.get_latest_instruction()
        # print("*" * 10, f"{self._setting}'s current memories: {memories}", "*" * 10)

        # 基于todo的类型，调用不同的action
        if isinstance(todo, Speak):
            rsp = await todo.run(profile=self.profile, name=self.name, context=memories, latest_instruction=latest_instruction)
            msg = Message(
                content=rsp, role=self.profile, sent_from=self.name,
                cause_by=Speak, send_to="", restricted_to="",
            )

        elif isinstance(todo, Verify):
            rsp = await todo.run(profile=self.profile, name=self.name, context=memories)
            msg = Message(
                content=rsp, role=self.profile, sent_from=self.name,
                cause_by=Verify, send_to="",
                restricted_to=f"Moderator,{self.profile}",
            )

        logger.info(f"{self._setting}: {rsp}")

        return msg
