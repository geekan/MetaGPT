from examples.werewolf_game.actions import InstructSpeak, Speak, Save, Poison
from examples.werewolf_game.roles.base_player import BasePlayer
from metagpt.schema import Message
from metagpt.logs import logger

class Witch(BasePlayer):
    def __init__(
        self,
        name: str = "",
        profile: str = "Witch",
        special_action_names: list[str] = ["Save", "Poison"],
        **kwargs,
    ):
        super().__init__(name, profile, special_action_names, **kwargs)

    async def _think(self):
        # 女巫涉及两个特殊技能，因此在此需要改写_think进行路由
        news = self._rc.news[0]
        assert news.cause_by == InstructSpeak # 消息为来自Moderator的指令时，才去做动作
        if not news.restricted_to:
            # 消息接收范围为全体角色的，做公开发言（发表投票观点也算发言）
            self._rc.todo = Speak()
        elif self.profile in news.restricted_to.split(","):
            # FIXME: hard code to split, restricted为"Moderator"或"Moderator,角色profile"
            # Moderator加密发给自己的，意味着要执行角色的特殊动作
            # 这里用关键词进行动作的选择，需要Moderator侧的指令进行配合
            if "save" in news.content.lower():
                self._rc.todo = Save()
            elif "poison" in news.content.lower():
                self._rc.todo = Poison()
            else:
                raise ValueError("Moderator's instructions must include save or poison keyword")

    async def _act(self):
        # todo为_think时确定的，有三种情况，Speak或Save或Poison
        todo = self._rc.todo
        logger.info(f"{self._setting}: ready to {str(todo)}")

        # 可以用这个函数获取该角色的全部记忆
        memories = self.get_all_memories()
        latest_instruction = self.get_latest_instruction()
        # print("*" * 10, f"{self._setting}'s current memories: {memories}", "*" * 10)

        # 根据自己定义的角色Action，对应地去run，run的入参可能不同
        if isinstance(todo, Speak):
            rsp = await todo.run(profile=self.profile, name=self.name, context=memories, latest_instruction=latest_instruction)
            msg = Message(
                content=rsp, role=self.profile, sent_from=self.name,
                cause_by=Speak, send_to="", restricted_to="",
            )

        elif isinstance(todo, Save):
            rsp = await todo.run(context=memories)
            msg = Message(
                content=rsp, role=self.profile, sent_from=self.name,
                cause_by=Save, send_to="",
                restricted_to=f"Moderator,{self.profile}", # 给Moderator发送要救的人的加密消息
            )

        elif isinstance(todo, Poison):
            rsp = await todo.run(context=memories)
            msg = Message(
                content=rsp, role=self.profile, sent_from=self.name,
                cause_by=Poison, send_to="",
                restricted_to=f"Moderator,{self.profile}", # 给Moderator发送要读的人的加密消息
            )

        logger.info(f"{self._setting}: {rsp}")

        return msg
