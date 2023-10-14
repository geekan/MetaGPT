import re

from examples.werewolf_game.memory.memory_retriever import MemoryRetriever
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
from examples.werewolf_game.actions import ACTIONS, InstructSpeak, Speak, Reflect, NighttimeWhispers
from examples.werewolf_game.actions.experience_operation import AddNewExperiences, RetrieveExperiences
from examples.werewolf_game.schema import RoleExperience

class BasePlayer(Role):
    def __init__(
        self,
        name: str = "PlayerXYZ",
        profile: str = "BasePlayer",
        special_action_names: list[str] = [],
        use_reflection: bool = True,
        use_experience: bool = False,
        use_memory_selection: bool = False,
        **kwargs,
    ):
        super().__init__(name, profile, **kwargs)
        # 通过 set_status() 更新状态。
        self.status = 0 # 0代表活着，1代表死亡

        # 技能和监听配置
        self._watch([InstructSpeak]) # 监听Moderator的指令以做行动
        special_actions = [ACTIONS[action_name] for action_name in special_action_names]
        capable_actions = [Speak] + special_actions
        self._init_actions(capable_actions) # 给角色赋予行动技能
        self.special_actions = special_actions

        self.use_reflection = use_reflection
        if not self.use_reflection and use_experience:
            logger.warning("You must enable use_reflection before using experience")
            self.use_experience = False
        else:
            self.use_experience = use_experience
        self.use_memory_selection = use_memory_selection

        self.experiences = []

        self.memory_retriever = MemoryRetriever(mode="heuristic")

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
        assert news.cause_by == InstructSpeak # 消息为来自Moderator的指令时，才去做动作
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
        memories = self.get_all_memories()
        latest_instruction = self.get_latest_instruction()
        # print("*" * 10, f"{self._setting}'s current memories: {memories}", "*" * 10)

        reflection = await Reflect().run(
            profile=self.profile, name=self.name, context=memories, latest_instruction=latest_instruction
        ) if self.use_reflection else ""

        experiences = RetrieveExperiences().run(query=reflection, profile=self.profile) \
            if self.use_experience else ""

        # 根据自己定义的角色Action，对应地去run，run的入参可能不同
        if isinstance(todo, Speak):
            rsp = await todo.run(
                profile=self.profile, name=self.name, context=memories,
                latest_instruction=latest_instruction, reflection=reflection, experiences=experiences)
            restricted_to = ""

        elif isinstance(todo, NighttimeWhispers):
            rsp = await todo.run(profile=self.profile, name=self.name, context=memories,
                reflection=reflection, experiences=experiences)
            restricted_to = f"Moderator,{self.profile}" # 给Moderator发送使用特殊技能的加密消息

        msg = Message(
            content=rsp, role=self.profile, sent_from=self.name,
            cause_by=type(todo), send_to="",
            restricted_to=restricted_to
        )

        self.experiences.append(
            RoleExperience(name=self.name, profile=self.profile, reflection=reflection,
                instruction=latest_instruction, response=rsp)
        )

        logger.info(f"{self._setting}: {rsp}")

        return msg

    def get_all_memories(self) -> str:
        if self.memory_retriever.mode == "full":
            memories = self.memory_retriever.get_full_memories(self._rc.memory, self.profile, self.name)
            return memories
        elif self.memory_retriever.mode == "heuristic":
            memories = self.memory_retriever.get_heuristic_memories(self._rc.memory, self.profile, self.name)
            return memories

    def get_latest_instruction(self) -> str:
        return self._rc.important_memory[-1].content # 角色监听着Moderator的InstructSpeak，是其重要记忆，直接获取即可

    def set_status(self, new_status):
        self.status = new_status

    def record_experiences(self, round_id: str, outcome: str, game_setup: str):
        experiences = [exp for exp in self.experiences if exp.reflection]
        for exp in experiences:
            exp.round_id = round_id
            exp.outcome = outcome
            exp.game_setup = game_setup
        AddNewExperiences().run(experiences)
