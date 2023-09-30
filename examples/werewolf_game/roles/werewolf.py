from examples.werewolf_game.roles.base_player import BasePlayer
from examples.werewolf_game.actions import Speak, Hunt
from metagpt.schema import Message
from metagpt.logs import logger

class Werewolf(BasePlayer):
    def __init__(
        self,
        name: str = "",
        profile: str = "Werewolf",
        special_action_names: list[str] = ["Hunt"],
        **kwargs,
    ):
        super().__init__(name, profile, special_action_names, **kwargs)

    async def _act(self):
        # todo为_think时确定的，有两种情况，Speak或Hunt
        todo = self._rc.todo
        logger.info(f"{self._setting}: ready to {str(todo)}")

        # 可以用这个函数获取该角色的全部记忆
        memories = self.get_all_memories()
        # print("*" * 10, f"{self._setting}'s current memories: {memories}", "*" * 10)

        # 根据自己定义的角色Action，对应地去run，run的入参可能不同
        if isinstance(todo, Speak):
            rsp = await todo.run(profile=self.profile, context=memories)
            msg = Message(
                content=rsp, role=self.profile, sent_from=self.name,
                cause_by=Speak, send_to="", restricted_to="",
            )

        elif isinstance(todo, Hunt):
            rsp = await todo.run(context=memories)
            msg = Message(
                content=rsp, role=self.profile, sent_from=self.name,
                cause_by=Hunt, send_to="",
                restricted_to=f"Moderator,{self.profile}", # 给Moderator及狼阵营发送要杀的人的加密消息
            )

        logger.info(f"{self._setting}: {rsp}")

        return msg
