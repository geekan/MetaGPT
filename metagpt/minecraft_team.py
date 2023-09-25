# -*- coding: utf-8 -*-
# @Date    : 2023/9/23 14:14
# @Author  : stellahong (stellahong@fuzhi.ai)
# @Desc    :
from typing import Iterable, Dict, Any
from pydantic import BaseModel, Field
import requests
import json
import time
import os

from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.software_company import SoftwareCompany

from metagpt.actions.minecraft.player_action import PlayerActions
from metagpt.roles.minecraft.minecraft_base import Minecraft
from metagpt.environment import Environment
import metagpt.utils.minecraft as U
from metagpt.utils.minecraft.process_monitor import SubprocessMonitor

class MineflayerEnv:
    def __init__(
        self,
        mc_port=None,
        server_host="http://127.0.0.1",
        server_port=3000,
        request_timeout=600,
    ):
        self.mc_port = mc_port
        self.server = f"{server_host}:{server_port}"
        self.server_port = server_port
        self.request_timeout = request_timeout
        self.mineflayer = self.get_mineflayer_process(server_port)
        self.has_reset = False
        self.reset_options = None
        self.connected = False
        self.server_paused = False

    def set_mc_port(self, mc_port):
        self.mc_port = mc_port

    def get_mineflayer_process(self, server_port):
        U.f_mkdir("./logs", "mineflayer")
        file_path = os.path.abspath(os.path.dirname(__file__))
        return SubprocessMonitor(
            commands=[
                "node",
                U.f_join(file_path, "mineflayer_env/mineflayer/index.js"),
                str(server_port),
            ],
            name="mineflayer",
            ready_match=r"Server started on port (\d+)",
            log_path=U.f_join("./logs", "mineflayer"),
        )

    def check_process(self):
        retry = 0
        while not self.mineflayer.is_running:
            logger.info("Mineflayer process has exited, restarting")
            self.mineflayer.run()
            if not self.mineflayer.is_running:
                if retry > 3:
                    logger.error("Mineflayer process failed to start")
                    raise {}
                else:
                    retry += 1
                    continue
            logger.info(self.mineflayer.ready_line)
            res = requests.post(
                f"{self.server}/start",
                json=self.reset_options,
                timeout=self.request_timeout,
            )
            if res.status_code != 200:
                self.mineflayer.stop()
                logger.error(
                    f"Minecraft server reply with code {res.status_code}"
                )
                raise {}
            return res.json()

    def reset(self, *, seed=None, options=None, ):
        if options is None:
            options = {}
        if options.get("inventory", {}) and options.get("mode", "hard") != "hard":
            logger.error("inventory can only be set when options is hard")
            raise{}

        self.reset_options = {
            "port": self.mc_port,
            "reset": options.get("mode", "hard"),
            "inventory": options.get("inventory", {}),
            "equipment": options.get("equipment", []),
            "spread": options.get("spread", False),
            "waitTicks": options.get("wait_ticks", 5),
            "position": options.get("position", None),
        }

        self.unpause()
        self.mineflayer.stop()
        time.sleep(1)  # wait for mineflayer to exit

        returned_data = self.check_process()
        self.has_reset = True
        self.connected = True
        # All the reset in step will be soft
        self.reset_options["reset"] = "soft"
        self.pause()
        return json.loads(returned_data)
    
    def close(self):
        self.unpause()
        if self.connected:
            res = requests.post(f"{self.server}/stop")
            if res.status_code == 200:
                self.connected = False
        self.mineflayer.stop()
        return not self.connected

    def pause(self):
        if self.mineflayer.is_running and not self.server_paused:
            res = requests.post(f"{self.server}/pause")
            if res.status_code == 200:
                self.server_paused = True
        return self.server_paused

    def unpause(self):
        if self.mineflayer.is_running and self.server_paused:
            res = requests.post(f"{self.server}/pause")
            if res.status_code == 200:
                self.server_paused = False
            else:
                print(res.json())
        return self.server_paused

class GameEnvironment(BaseModel, arbitrary_types_allowed=True):
    """
    游戏环境的记忆，用于多个agent进行信息的共享和缓存，而不需要重复在自己的角色内维护缓存
    """
    event: dict[str, Any] = Field(default_factory=dict)
    current_task: str = Field(default="Craft 4 wooden planks")
    task_execution_time: float = Field(default=float)
    context: str = Field(default="")

    code: str = Field(default="")
    programs: str = Field(default="")

    mf_instance : MineflayerEnv = Field(default_factory=MineflayerEnv)

    def set_mc_port(self, mc_port):
        self.mf_instance.set_mc_port(mc_port)
    
    def register_roles(self, roles: Iterable[Minecraft]):
        for role in roles:
            role.set_memory(self)
    
    def update_event(self, event: Dict):
        self.event = event
    
    def update_task(self, task: str):
        self.current_task = task
    
    def update_context(self, context: str):
        self.context = context

    def update_code(self, code: str):
        self.code = code

    def update_program(self, programs: str):
        self.programs = programs

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
            # Example: events = minecraft_api.get_events()
            if not self.mf_instance.has_reset:
                # TODO Modify
                logger.info("Environment has not been reset yet, is resetting")
                self.mf_instance.reset(options={
                    "mode": "soft",
                    "wait_ticks": 20,
                })
                # raise {}
            self.mf_instance.check_process()
            self.mf_instance.unpause()
            data = {
                "code": self.code,
                "programs": self.programs,
            }
            res = requests.post(
                f"{self.mf_instance.server}/step", json=data, timeout=self.mf_instance.request_timeout
            )
            if res.status_code != 200:
                logger.error("Failed to step Minecraft server")
                raise {}
            returned_data = res.json()
            self.mf_instance.pause()
            events = json.loads(returned_data)
            logger.info(f"Get Current Event: {events}")
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
    game_memory: GameEnvironment = Field(default_factory=GameEnvironment)
    investment: float = Field(default=50.0)
    task: str = Field(default="")
    game_info: dict = Field(default={})
    
    def set_port(self, mc_port):
        self.game_memory.set_mc_port(mc_port)

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

if "__name__" == "__main__":
    test_code = "bot.chat(`/time set ${getNextTime()}`);"
    mc_port = 1960
    # env_wait_ticks = 20
    ge = GameEnvironment()
    ge.set_mc_port(mc_port)
    ge.update_code(test_code)
    # ge.mf_instance.reset(options={
    #             "mode": "soft",
    #             "wait_ticks": env_wait_ticks,
    #         })
    logger.info(ge.on_event())