from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
from examples.werewolf_game.actions import ACTIONS, Speak, InstructSpeak

ROLE_STATES = {
    # 存活状态
    0: "Alive", # 开场
    1: "Dead", # 结束
    2: "Protected", # 被保护
    3: "Poisoned", # 被毒
    4: "Saved", # 被救
    5: "Killed" # 被刀
}

class BasePlayer(Role):
    def __init__(
        self,
        name: str = "PlayerXYZ",
        profile: str = "BasePlayer",
        team: str = "good guys",
        special_action_names: list[str] = [],
        **kwargs,
    ):
        super().__init__(name, profile, **kwargs)
        self._init_actions([Speak])
        self._watch([InstructSpeak])
        self.team = team
        # 调用 get_status() 来检查存活状态,并通过 set_status() 更新状态。
        self.status = 0 # 初始状态为活着
        
        # 技能和监听配置
        self._watch([InstructSpeak]) # 监听Moderator的指令以做行动
        special_actions = [ACTIONS[action_name] for action_name in special_action_names]
        capable_actions = [Speak] + special_actions
        self._init_actions(capable_actions) # 给角色赋予行动技能
        self.special_actions = special_actions
    
    async def _observe(self) -> int:
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
        elif self.profile in news.restricted_to.split(","): # FIXME: hard code to split, restricted为"Moderator"或"Moderator,角色profile"
            # Moderator加密发给自己的，意味着要执行角色的特殊动作
            self._rc.todo = self.special_actions[0]()

    async def _act(self):
        """每个角色要改写此函数以实现该角色的动作"""
        raise NotImplementedError
    
    def get_all_memories(self) -> str:
        memories = self._rc.memory.get()
        memories = [f"{m.sent_from}: {m.content}" for m in memories]
        memories = "\n".join(memories)
        return memories
 
    def get_name(self):
        return self.name

    def get_profile(self):
        return self.profile

    def get_team(self):
        return self.team

    def get_status(self):
        return self.status

    def set_status(self, new_status):
        self.status = new_status
