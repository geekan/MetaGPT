# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 14:29
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import json

from metagpt.logs import logger

from metagpt.roles.minecraft.minecraft_base import Minecraft as Base
from metagpt.schema import Message
from metagpt.actions.minecraft.player_action import PlayerActions
from metagpt.actions.minecraft.generate_actions import GenerateActionCode
from metagpt.actions.minecraft.process_event import HandleEvents


class EventHandler(Base):
    def __init__(
            self,
            name: str = "Thompson",
            profile: str = "Minecraft Event Handler",
            goal: str = "To efficiently manage and respond to in-game events, providing information about the player.",
            constraints: str = "Resource availability, server performance, adherence to server rules and regulations.",
    ) -> None:
        super().__init__(name, profile, goal, constraints)
        # Initialize actions specific to the EventHandler role
        self._init_actions([HandleEvents])
        
        # Set events or actions the EventHandler should watch or be aware of
        self._watch([PlayerActions, GenerateActionCode])
        self.last_events = {"env_events": {},
                            "execute_results": {}}
    

    async def _act(self) -> Message:
        # 获取最新的消息
        
        msg = self._rc.memory.get(k=1)[0]
        query = msg.content if self._rc.state == 0 else msg.instruct_content
        """
        todo: parse query info from message, e.g. test_round and action code
        """
        test_round = 1
        logger.info(msg.cause_by)
      
        if msg.cause_by == GenerateActionCode:  # 进行生成的代码执行, 获取的结果用于进行AI评估
            events = await HandleEvents().run(query)
            result_msg = Message(
                content=f"Round {test_round} of rollout done",
                role=self.profile,
                cause_by=HandleEvents,
                sent_from=self.profile,
                send_to="Task Reviewer",
            )
           
            self.perform_game_info_callback(events, self.game_memory.update_event)
            
        else:
            events = await HandleEvents().run(query)
            result_msg = Message(
                content=events,
                role=self.profile,
                cause_by=HandleEvents,
                sent_from=self.profile,
                send_to="",
            )
            
        self.perform_game_info_callback(events, self.game_memory.update_event)
        return result_msg
