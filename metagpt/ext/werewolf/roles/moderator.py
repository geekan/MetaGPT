import re
from datetime import datetime
from typing import Union

from metagpt.actions.add_requirement import UserRequirement
from metagpt.const import DEFAULT_WORKSPACE_ROOT, MESSAGE_ROUTE_TO_ALL
from metagpt.environment.werewolf.const import (
    STEP_INSTRUCTIONS,
    RoleActionRes,
    RoleState,
    RoleType,
)
from metagpt.environment.werewolf.env_space import EnvAction, EnvActionType
from metagpt.ext.werewolf.actions import Hunt, Poison, Protect, Save, Verify
from metagpt.ext.werewolf.actions.moderator_actions import (
    AnnounceGameResult,
    InstructSpeak,
    ParseSpeak,
)
from metagpt.ext.werewolf.roles.base_player import BasePlayer
from metagpt.ext.werewolf.schema import WwMessage
from metagpt.logs import logger
from metagpt.utils.common import any_to_str


class Moderator(BasePlayer):
    name: str = RoleType.MODERATOR.value
    profile: str = RoleType.MODERATOR.value

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._watch([UserRequirement, InstructSpeak, ParseSpeak])
        self.set_actions([InstructSpeak, ParseSpeak, AnnounceGameResult])

        # game states
        self.step_idx = 0
        self.game_setup = ""
        self.werewolf_players = []
        self.winner = None
        self.win_reason = None
        self.witch_poison_left = 1
        self.witch_antidote_left = 1

    def update_player_status(self, player_names: list[str]):
        if not player_names:
            return
        roles_in_env = self.rc.env.get_roles()
        for role_setting, role in roles_in_env.items():
            for player_name in player_names:
                if player_name in role_setting:
                    role.set_status(new_status=RoleState.DEAD)  # 更新为死亡

    def _record_all_experiences(self):
        logger.info(f"The winner of the game: {self.winner}, start to record roles' experiences")
        roles_in_env = self.rc.env.get_roles()
        timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        for _, role in roles_in_env.items():
            if role == self:
                continue
            if self.winner == "werewolf":
                outcome = "won" if role.profile in RoleType.WEREWOLF.value else "lost"
            else:
                outcome = "won" if role.profile not in RoleType.WEREWOLF.value else "lost"
            role.record_experiences(round_id=timestamp, outcome=outcome, game_setup=self.game_setup)

    async def _parse_speak(self, memories):
        latest_msg = memories[-1]
        latest_msg_content = latest_msg.content

        match = re.search(r"Player[0-9]+", latest_msg_content[-10:])  # FIXME: hard code truncation
        target = match.group(0) if match else ""

        # default return
        msg_content = "Understood"
        restricted_to = set()

        msg_cause_by = latest_msg.cause_by
        if msg_cause_by == any_to_str(Hunt):
            self.rc.env.step(
                EnvAction(
                    action_type=EnvActionType.WOLF_KILL, player_name=latest_msg.sent_from, target_player_name=target
                )
            )
        elif msg_cause_by == any_to_str(Protect):
            self.rc.env.step(
                EnvAction(
                    action_type=EnvActionType.GUARD_PROTECT, player_name=latest_msg.sent_from, target_player_name=target
                )
            )
        elif msg_cause_by == any_to_str(Verify):
            if target in self.werewolf_players:
                msg_content = f"{target} is a werewolf"
            else:
                msg_content = f"{target} is a good guy"
            restricted_to = {RoleType.MODERATOR.value, RoleType.SEER.value}
        elif msg_cause_by == any_to_str(Save):
            if RoleActionRes.PASS.value in latest_msg_content.lower():
                # the role ignore to response, answer `pass`
                pass
            elif not self.witch_antidote_left:
                msg_content = "You have no antidote left and thus can not save the player"
                restricted_to = {RoleType.MODERATOR.value, RoleType.WITCH.value}
            else:
                self.rc.env.step(
                    EnvAction(
                        action_type=EnvActionType.WITCH_SAVE,
                        player_name=latest_msg.sent_from,
                        target_player_name=target,
                    )
                )
        elif msg_cause_by == any_to_str(Poison):
            if RoleActionRes.PASS.value in latest_msg_content.lower():
                pass
            elif not self.witch_poison_left:
                msg_content = "You have no poison left and thus can not poison the player"
                restricted_to = {RoleType.MODERATOR.value, RoleType.WITCH.value}
            else:
                self.rc.env.step(
                    EnvAction(
                        action_type=EnvActionType.WITCH_POISON,
                        player_name=latest_msg.sent_from,
                        target_player_name=target,
                    )
                )

        return msg_content, restricted_to

    def _update_player_status(self, step_idx: int, player_current_dead: list[str]):
        """update dead player's status"""
        if step_idx in [15, 18]:
            self.update_player_status(player_current_dead)

    def _record_game_history(self, step_idx: int):
        if step_idx and step_idx % len(STEP_INSTRUCTIONS) == 0 or self.winner:
            logger.info("a night and day cycle completed, examine all history")
            logger.debug(f"all_memories: {self.get_all_memories()}")
            with open(DEFAULT_WORKSPACE_ROOT / "werewolf_transcript.txt", "w") as f:
                f.write(self.get_all_memories())

    async def _observe(self, ignore_memory=False) -> int:
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
        # add `MESSAGE_ROUTE_TO_ALL in n.send_to` make it to run `ParseSpeak`
        self.rc.news = [
            n
            for n in news
            if (n.cause_by in self.rc.watch or self.profile in n.send_to or MESSAGE_ROUTE_TO_ALL in n.send_to)
            and n not in old_messages
        ]
        return len(self.rc.news)

    async def _think(self):
        if self.winner:
            self.rc.todo = AnnounceGameResult()
            return

        latest_msg = self.rc.memory.get()[-1]
        if latest_msg.role in ["User", "Human", self.profile]:
            # 1. 上一轮消息是用户指令，解析用户指令，开始游戏
            # 2.1. 上一轮消息是Moderator自己的指令，继续发出指令，一个事情可以分几条消息来说
            # 2.2. 上一轮消息是Moderator自己的解析消息，一个阶段结束，发出新一个阶段的指令
            self.rc.todo = InstructSpeak()
        else:
            # 上一轮消息是游戏角色的发言，解析角色的发言
            self.rc.todo = ParseSpeak()

    def _init_fields_from_obj(self, obs: dict[str, Union[int, str, list[str]]]):
        self.game_setup = obs.get("game_setup", "")
        self.step_idx = obs.get("step_idx", 0)
        self.winner = obs.get("winner")
        self.win_reason = obs.get("win_reason")
        self.werewolf_players = obs.get("werewolf_players", [])
        self.witch_poison_left = obs.get("witch_poison_left", 0)
        self.witch_antidote_left = obs.get("witch_antidote_left", 0)

    async def _act(self):
        todo = self.rc.todo
        logger.info(f"{self._setting} ready to {todo}")

        memories = self.get_all_memories(mode="msg")

        obs, _, _, _, _ = self.rc.env.step(action=EnvAction(action_type=EnvActionType.NONE))
        living_players = obs["living_players"]
        werewolf_players = obs["werewolf_players"]
        player_hunted = obs["player_hunted"]
        player_current_dead = obs["player_current_dead"]
        self._init_fields_from_obj(obs)

        # 若进行完一夜一日的循环，打印和记录一次完整发言历史
        self._record_game_history(self.step_idx)

        # 若一晚或一日周期结束，对当晚或当日的死者进行总结，并更新玩家状态
        self._update_player_status(self.step_idx, player_current_dead)
        if self.winner:
            self._record_all_experiences()

        # 根据_think的结果，执行InstructSpeak还是ParseSpeak, 并将结果返回
        if isinstance(todo, InstructSpeak):
            msg_content, msg_to_send_to, msg_restricted_to = await InstructSpeak().run(
                self.step_idx,
                living_players=living_players,
                werewolf_players=werewolf_players,
                player_hunted=player_hunted,
                player_current_dead=player_current_dead,
            )
            # msg_content = f"Step {self.step_idx}: {msg_content}" # HACK: 加一个unique的step_idx避免记忆的自动去重
            msg = WwMessage(
                content=msg_content,
                role=self.profile,
                sent_from=self.name,
                cause_by=InstructSpeak,
                send_to=msg_to_send_to,
                restricted_to=msg_restricted_to,
            )
            logger.info(f"current step_idx: {self.step_idx}")
            self.rc.env.step(EnvAction(action_type=EnvActionType.PROGRESS_STEP))  # to update step_idx

        elif isinstance(todo, ParseSpeak):
            msg_content, msg_restricted_to = await self._parse_speak(memories)
            # msg_content = f"Step {self.step_idx}: {msg_content}" # HACK: 加一个unique的step_idx避免记忆的自动去重
            msg = WwMessage(
                content=msg_content,
                role=self.profile,
                sent_from=self.name,
                cause_by=ParseSpeak,
                send_to={},
                restricted_to=msg_restricted_to,
            )

        elif isinstance(todo, AnnounceGameResult):
            msg_content = await AnnounceGameResult().run(winner=self.winner, win_reason=self.win_reason)
            msg = WwMessage(content=msg_content, role=self.profile, sent_from=self.name, cause_by=AnnounceGameResult)

        logger.info(f"{self._setting}: {msg_content}")

        return msg

    def get_all_memories(self, mode="str") -> str:
        memories = self.rc.memory.get()
        if mode == "str":
            memories = [f"{m.sent_from}({m.role}): {m.content}" for m in memories]
            memories = "\n".join(memories)
        return memories
