import re

from pydantic import Field, SerializeAsAny, model_validator

from metagpt.actions.action import Action
from metagpt.environment.werewolf.const import RoleState, RoleType
from metagpt.ext.werewolf.actions import (
    ACTIONS,
    AddNewExperiences,
    InstructSpeak,
    NighttimeWhispers,
    Reflect,
    RetrieveExperiences,
    Speak,
)
from metagpt.ext.werewolf.schema import RoleExperience, WwMessage
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.utils.common import any_to_str


class BasePlayer(Role):
    name: str = "PlayerXYZ"
    profile: str = "BasePlayer"
    special_action_names: list[str] = []
    use_reflection: bool = True
    use_experience: bool = False
    use_memory_selection: bool = False
    new_experience_version: str = ""
    status: RoleState = RoleState.ALIVE

    special_actions: list[SerializeAsAny[Action]] = Field(default=[], validate_default=True)
    experiences: list[RoleExperience] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 技能和监听配置
        self._watch([InstructSpeak])  # 监听Moderator的指令以做行动
        special_actions = [ACTIONS[action_name] for action_name in self.special_action_names]
        capable_actions = [Speak] + special_actions
        self.set_actions(capable_actions)  # 给角色赋予行动技能
        self.special_actions = special_actions

        if not self.use_reflection and self.use_experience:
            logger.warning("You must enable use_reflection before using experience")
            self.use_experience = False

    @model_validator(mode="after")
    def check_addresses(self):
        if not self.addresses:
            self.addresses = {any_to_str(self), self.name, self.profile} if self.name else {any_to_str(self)}
        return self

    async def _observe(self, ignore_memory=False) -> int:
        if self.status != RoleState.ALIVE:
            # 死者不再参与游戏
            return 0
        news = []
        if not news:
            news = self.rc.msg_buffer.pop_all()
        old_messages = [] if ignore_memory else self.rc.memory.get()
        for m in news:
            if len(m.restricted_to) and self.profile not in m.restricted_to and self.name not in m.restricted_to:
                # if the msg is not send to the whole audience ("") nor this role (self.profile or self.name),
                # then this role should not be able to receive it and record it into its memory
                continue
            self.rc.memory.add(m)
        self.rc.news = [
            n for n in news if (n.cause_by in self.rc.watch or self.profile in n.send_to) and n not in old_messages
        ]

        # TODO to delete
        # await super()._observe()
        # # 只有发给全体的（""）或发给自己的（self.profile）消息需要走下面的_react流程，
        # # 其他的收听到即可，不用做动作
        # self.rc.news = [msg for msg in self.rc.news if msg.send_to in ["", self.profile]]
        return len(self.rc.news)

    async def _think(self):
        news = self.rc.news[0]
        assert news.cause_by == any_to_str(InstructSpeak)  # 消息为来自Moderator的指令时，才去做动作
        if not news.restricted_to:
            # 消息接收范围为全体角色的，做公开发言（发表投票观点也算发言）
            self.rc.todo = Speak()
        elif self.profile in news.restricted_to:
            # FIXME: hard code to split, restricted为"Moderator"或"Moderator, 角色profile"
            # Moderator加密发给自己的，意味着要执行角色的特殊动作
            self.rc.todo = self.special_actions[0]()
        return True

    async def _act(self):
        # todo为_think时确定的，有两种情况，Speak或Protect
        todo = self.rc.todo
        logger.info(f"{self._setting}: ready to {str(todo)}")

        # 可以用这个函数获取该角色的全部记忆和最新的instruction
        memories = self.get_all_memories()
        latest_instruction = self.get_latest_instruction()

        reflection = (
            await Reflect().run(
                profile=self.profile, name=self.name, context=memories, latest_instruction=latest_instruction
            )
            if self.use_reflection
            else ""
        )

        experiences = (
            RetrieveExperiences().run(
                query=reflection, profile=self.profile, excluded_version=self.new_experience_version
            )
            if self.use_experience
            else ""
        )

        # 根据自己定义的角色Action，对应地去run，run的入参可能不同
        if isinstance(todo, Speak):
            rsp = await todo.run(
                profile=self.profile,
                name=self.name,
                context=memories,
                latest_instruction=latest_instruction,
                reflection=reflection,
                experiences=experiences,
            )
            restricted_to = set()

        elif isinstance(todo, NighttimeWhispers):
            rsp = await todo.run(
                profile=self.profile, name=self.name, context=memories, reflection=reflection, experiences=experiences
            )
            restricted_to = {RoleType.MODERATOR.value, self.profile}  # 给Moderator发送使用特殊技能的加密消息
        msg = WwMessage(
            content=rsp,
            role=self.profile,
            sent_from=self.name,
            cause_by=type(todo),
            send_to={},
            restricted_to=restricted_to,
        )

        self.experiences.append(
            RoleExperience(
                name=self.name,
                profile=self.profile,
                reflection=reflection,
                instruction=latest_instruction,
                response=rsp,
                version=self.new_experience_version,
            )
        )

        logger.info(f"{self._setting}: {rsp}")

        return msg

    def get_all_memories(self) -> str:
        memories = self.rc.memory.get()
        time_stamp_pattern = r"[0-9]+ \| "
        # NOTE: 除Moderator外，其他角色使用memory，只能用m.sent_from（玩家名）不能用m.role（玩家角色），因为他们不知道说话者的身份
        memories = [f"{m.sent_from}: {re.sub(time_stamp_pattern, '', m.content)}" for m in memories]  # regex去掉时间戳
        memories = "\n".join(memories)
        return memories

    def get_latest_instruction(self) -> str:
        return self.rc.important_memory[-1].content  # 角色监听着Moderator的InstructSpeak，是其重要记忆，直接获取即可

    def set_status(self, new_status: RoleState):
        self.status = new_status

    def record_experiences(self, round_id: str, outcome: str, game_setup: str):
        experiences = [exp for exp in self.experiences if len(exp.reflection) > 2]  # not "" or not '""'
        for exp in experiences:
            exp.round_id = round_id
            exp.outcome = outcome
            exp.game_setup = game_setup
        AddNewExperiences().run(experiences)
