from examples.werewolf_game.roles.base_player import BasePlayer
from examples.werewolf_game.actions import Speak
from metagpt.schema import Message
from metagpt.logs import logger

class Villager(BasePlayer):
    def __init__(
        self,
        name: str = "",
        profile: str = "Villager",
        special_action_names: list[str] = [],
        **kwargs,
    ):
        super().__init__(name, profile, special_action_names, **kwargs)

    async def _act(self):

        # todo为_think时确定的，在村民这里，就只有一种todo，即Speak
        todo = self._rc.todo
        logger.info(f"{self._setting}: ready to {todo}")

        # 可以用这个函数获取该角色的全部记忆
        memories = self.get_all_memories()
        # print("*" * 10, f"{self._setting}'s current memories: {memories}", "*" * 10)

        # 根据自己定义的角色Action，对应地去run
        rsp = await todo.run(profile=self.profile, context=memories)

        # 返回消息，注意给Moderator发送的加密消息需要用restricted_to="Moderator"
        msg = Message(
            content=rsp, role=self.profile, sent_from=self.name,
            cause_by=Speak, send_to="", restricted_to="",
        )

        logger.info(f"{self._setting}: {rsp}")

        return msg
