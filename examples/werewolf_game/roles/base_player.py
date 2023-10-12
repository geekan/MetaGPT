import re

from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
from examples.werewolf_game.actions import ACTIONS, InstructSpeak, Speak, Reflect, NighttimeWhispers


class BasePlayer(Role):
    def __init__(
            self,
            name: str = "PlayerXYZ",
            profile: str = "BasePlayer",
            special_action_names: list[str] = [],
            **kwargs,
    ):
        super().__init__(name, profile, **kwargs)
        # 通过 set_status() 更新状态。
        self.status = 0  # 0代表活着，1代表死亡

        # 技能和监听配置
        self._watch([InstructSpeak])  # 监听Moderator的指令以做行动
        special_actions = [ACTIONS[action_name] for action_name in special_action_names]
        capable_actions = [Speak] + special_actions
        self._init_actions(capable_actions)  # 给角色赋予行动技能
        self.special_actions = special_actions

    async def _observe(self) -> int:
        if self.status == 1:
            # 死者不再参与游戏
            return 0

        await super()._observe()
        # 只有发给全体的（""）或发给自己的（self.profile）消息需要走下面的_react流程，
        # 其他的收听到即可，不用做动作
        self._rc.news = [msg for msg in self._rc.news if msg.send_to in ["", self.profile]]
        return len(self._rc.news)

    async def _think(self):
        news = self._rc.news[0]
        assert news.cause_by == InstructSpeak  # 消息为来自Moderator的指令时，才去做动作
        if not news.restricted_to:
            # 消息接收范围为全体角色的，做公开发言（发表投票观点也算发言）
            self._rc.todo = Speak()
        elif self.profile in news.restricted_to.split(","):
            # FIXME: hard code to split, restricted为"Moderator"或"Moderator,角色profile"
            # Moderator加密发给自己的，意味着要执行角色的特殊动作
            self._rc.todo = self.special_actions[0]()

    async def _act(self):

        # todo为_think时确定的，有两种情况，Speak或Protect
        todo = self._rc.todo
        logger.info(f"{self._setting}: ready to {str(todo)}")

        # 可以用这个函数获取该角色的全部记忆和最新的instruction
        memories = self.get_all_memories(mode="heuristic")
        latest_instruction = self.get_latest_instruction()
        # print("*" * 10, f"{self._setting}'s current memories: {memories}", "*" * 10)

        reflection = await Reflect().run(
            profile=self.profile, name=self.name, context=memories, latest_instruction=latest_instruction
        )

        # 根据自己定义的角色Action，对应地去run，run的入参可能不同
        if isinstance(todo, Speak):
            rsp = await todo.run(
                profile=self.profile, name=self.name, context=memories,
                latest_instruction=latest_instruction, reflection=reflection
            )
            restricted_to = ""

        elif isinstance(todo, NighttimeWhispers):
            rsp = await todo.run(profile=self.profile, name=self.name, context=memories, reflection=reflection)
            restricted_to = f"Moderator,{self.profile}"  # 给Moderator发送使用特殊技能的加密消息

        msg = Message(
            content=rsp, role=self.profile, sent_from=self.name,
            cause_by=type(todo), send_to="",
            restricted_to=restricted_to
        )

        logger.info(f"{self._setting}: {rsp}")

        return msg

    def get_all_memories(self, mode="full") -> str:
        if mode == "full":
            memories = self.get_memories_full()
            return memories
        elif mode == "heuristic":
            memories = self.get_memories_heuristic()
            return memories

    def get_memories_full(self) -> str:
        memories = self._rc.memory.get()
        time_stamp_pattern = r'[0-9]+ \| '
        # NOTE: 除Moderator外，其他角色使用memory，只能用m.sent_from（玩家名）不能用m.role（玩家角色），因为他们不知道说话者的身份
        memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in memories]  # regex去掉时间戳
        memories = "\n".join(memories)
        return memories

    def get_memories_heuristic(self, m=20, n=10) -> str:
        all_memories = self._rc.memory.get()

        recent_m_memories = all_memories[-m:]   # 取最近m条记忆

        # 将所有记忆按照重要性打分
        scored_memories = [(message, self.score_message(message.content)) for message in all_memories]

        # 提取分数最高的n条记忆，如果分数相同，则较新时间的记忆排在前面
        # sorted_memories = sorted(scored_memories, key=lambda x: x[1], reverse=True)
        sorted_memories = sorted(scored_memories, key=lambda x: (x[1], scored_memories.index(x)),
                                 reverse=True)

        # FIXME 如果informative记忆与recent记忆有重合，则在informative中去掉重合的recent记忆？
        top_n_informative_memories = [memory[0] for memory in sorted_memories[:n]]
        # top_n_informative_memories = [memory[0] for memory in sorted_memories[:n] if memory[0] not in recent_m_memories]

        time_stamp_pattern = r'[0-9]+ \| '

        recent_memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in
                           recent_m_memories]
        informative_memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in
                                top_n_informative_memories]

        memories = "Recent Messages:\n" + "\n".join(recent_memories) + "\n\nInformative Messages:\n" + "\n".join(
            informative_memories)

        return memories

    def score_message(self, message: str) -> int:
        # Score 5: Information related to the player's character
        pattern_5 = rf"({self.name}|{self.profile})"
        if re.search(pattern_5, message, re.IGNORECASE):
            return 5

        # Score 4: Keywords related to elimination or death
        pattern_4 = r"(die(d|s)?|banish(ed)?|vote(d|s)? out|eliminat(e|ed|ion)?|kill(ed)?|hunt(ed)?)"
        if re.search(pattern_4, message, re.IGNORECASE):
            return 4

        # Score 3: Keywords related to speculation or guessing
        pattern_3 = r"(discover(ed)?|speculat(e|ed|ion)?|guess(ed)?|conjectur(e|ed)?|doubt(ed)?|verif(y|ied|ication)?)"
        if re.search(pattern_3, message, re.IGNORECASE):
            return 3

        # Score 2: Keywords related to specific actions
        pattern_2 = r"(protect(ed|s)?|save(d|s)?|verif(y|ied)|drug(s)?|antidote|poison(ed|s)?)"

        if re.search(pattern_2, message, re.IGNORECASE):
            return 2

        # Score 1: Other messages
        else:
            return 1

    def get_latest_instruction(self) -> str:
        return self._rc.important_memory[-1].content  # 角色监听着Moderator的InstructSpeak，是其重要记忆，直接获取即可

    def set_status(self, new_status):
        self.status = new_status
