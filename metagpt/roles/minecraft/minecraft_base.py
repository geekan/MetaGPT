# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 21:38
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
import contextlib
import json

from metagpt.logs import logger
from metagpt.roles.role import Role
from metagpt.schema import HumanMessage, SystemMessage

from typing import Dict

from pydantic import BaseModel


class Registry(BaseModel):
    """Registry for storing and building classes."""

    name: str
    entries: Dict = {}

    def register(self, key: str):
        def decorator(class_builder):
            self.entries[key] = class_builder
            return class_builder

        return decorator

    def build(self, type: str, **kwargs):
        if type not in self.entries:
            raise ValueError(
                f'{type} is not registered. Please register with the .register("{type}") method provided in {self.name} registry'
            )
        return self.entries[type](**kwargs)

    def get_all_entries(self):
        return self.entries
    
class Minecraft(Role):
    def __init__(
            self,
            name: str = "MC",
            profile: str = "Minecraft Role",
            goal: str = "",
            constraints: str = "",
    ) -> None:
        super().__init__(name, profile, goal, constraints)
        self.game_memory = None
        self.event = {}

    
    #
    async def _think(self) -> None:
        if len(self._actions) == 1:
            # If there is only one action, then only this one can be performed
            self._set_state(0)
            return True
        
        if self._rc.todo is None:
            logger.info("0")
            self._set_state(0)
            return True
        
        if self._rc.state + 1 < len(self._states):
            self._set_state(self._rc.state + 1)
            logger.info("1")
            return True
        else:
            self._rc.todo = None
            logger.info("2")
            
            return False
    
    async def _obtain_events(self):
        return await self.game_memory.on_event()
    
    def set_memory(self, shared_memory: 'GameMemory'):
        self.game_memory = shared_memory
    
    def render_human_message(self, msg, *args, **kwargs):
        return HumanMessage(content=msg)
    
    def render_system_message(self, msg, *args, **kwargs):
        return SystemMessage(content=msg)
    
    @staticmethod
    def perform_game_info_callback(info: object, callback: object) -> object:
        logger.debug(info)
        callback(info)
    
    def encapsule_message(self, msg, *args, **kwargs):
        human_msg = self.render_human_message(msg, *args, **kwargs)
        system_msg = self.render_system_message(msg, *args, **kwargs)
        return {"system_msg": [system_msg.content],
                "human_msg": human_msg.content}

agent_registry = Registry(name="Minecraft")

if __name__ == "__main__":
    mc = Minecraft()
    result = "Async operation result"
    # 调用回调函数，并传递结果
    # mc.perform_memory_callback(mc.my_callback)
    print(mc.game_memory.current_task)
