# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 14:14
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from typing import Iterable, Dict, Any
from pydantic import BaseModel, Field

from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.software_company import SoftwareCompany

from metagpt.actions.minecraft.player_action import PlayerActions
from metagpt.roles.minecraft.minecraft_base import Minecraft
from metagpt.environment import Environment


class GameMemory(BaseModel):
    """
    游戏环境的记忆，用于多个agent进行信息的共享和缓存，而不需要重复在自己的角色内维护缓存
    """
    event: dict[str, Any] = Field(default_factory=dict)
    current_task: str = Field(default="Craft 4 wooden planks")
    task_execution_time: float = Field(default=float)
    context: str = Field(default="")
    
    def register_roles(self, roles: Iterable[Minecraft]):
        for role in roles:
            role.set_memory(self)
    
    def update_event(self, event: Dict):
        self.event = event
    
    def update_task(self, task: str):
        self.current_task = task
    
    def update_context(self, context: str):
        self.context = context
    
    async def on_event(self, *args):
        """
        Retrieve Minecraft events.

        This function is used to obtain events from the Minecraft environment. Check the implementation in
        the 'voyager/env/bridge.py step()' function to capture events generated within the game.

        Returns:
            list: A list of Minecraft events.

            Raises:
                Exception: If there is an issue retrieving events.
        """
        try:
            # Implement the logic to retrieve Minecraft events here.
            events = {
                "Biome": "river",
                "Time": "night",
                "Nearby blocks": "water, dirt, stone, coal_ore, sandstone, grass_block, sand, grass, oak_leaves, fern, seagrass, tall_seagrass",
                "Nearby entities(nearest to  farthest)": "turtle, salmon",
                "Health": "20.0 / 20",
                "Hunger": "20.0 / 20",
                "Position": "x = -47.5, y = 63.0, z = -283.5",
                "Equipment": [],
                "Inventory(0 / 36)": "Empty",
                "Chests": ""
            }
            # Example: events = minecraft_api.get_events()
            
            return events
        except Exception as e:
            logger.error(f"Failed to retrieve Minecraft events: {str(e)}")
            raise {}


class MinecraftPlayer(SoftwareCompany):
    """
    Software Company: Possesses a team, SOP (Standard Operating Procedures), and a platform for instant messaging,
    dedicated to writing executable code.
    """
    environment: Environment = Field(default_factory=Environment)
    game_memory: GameMemory = Field(default_factory=GameMemory)
    investment: float = Field(default=50.0)
    task: str = Field(default="")
    game_info: dict = Field(default={})
    
    def hire(self, roles: list[Role]):
        self.environment.add_roles(roles)
        self.game_memory.register_roles(roles)
    
    def start(self, task):
        """Start a project from publishing boss requirement."""
        self.task = task
        self.environment.publish_message(Message(role="Player", content=task, cause_by=PlayerActions))
        logger.info(self.game_info)
    
    def _save(self):
        logger.info(self.json())
    
    async def run(self, n_round=3):
        """Run company until target round or no money"""
        while n_round > 0:
            # self._save()
            n_round -= 1
            logger.debug(f"{n_round=}")
            self._check_balance()
            await self.environment.run()
        
        return self.environment.history


