#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : The Minecraft external environment to integrate with Minecraft game
#           refs to `voyager bridge.py`

import json
import time
from typing import Any, Optional

import requests
from pydantic import ConfigDict, Field, model_validator

from metagpt.environment.base_env import ExtEnv, mark_as_writeable
from metagpt.environment.base_env_space import BaseEnvAction, BaseEnvObsParams
from metagpt.environment.minecraft.const import (
    MC_CKPT_DIR,
    MC_CORE_INVENTORY_ITEMS,
    MC_CURRICULUM_OB,
    MC_DEFAULT_WARMUP,
    METAGPT_ROOT,
)
from metagpt.environment.minecraft.process_monitor import SubprocessMonitor
from metagpt.logs import logger


class MinecraftExtEnv(ExtEnv):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    mc_port: Optional[int] = Field(default=None)
    server_host: str = Field(default="http://127.0.0.1")
    server_port: str = Field(default=3000)
    request_timeout: int = Field(default=600)

    mineflayer: Optional[SubprocessMonitor] = Field(default=None, validate_default=True)

    has_reset: bool = Field(default=False)
    reset_options: Optional[dict] = Field(default=None)
    connected: bool = Field(default=False)
    server_paused: bool = Field(default=False)
    warm_up: dict = Field(default=dict())

    def reset(
        self,
        *,
        seed: Optional[int] = None,
        options: Optional[dict[str, Any]] = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        pass

    def observe(self, obs_params: Optional[BaseEnvObsParams] = None) -> Any:
        pass

    def step(self, action: BaseEnvAction) -> tuple[dict[str, Any], float, bool, bool, dict[str, Any]]:
        pass

    @property
    def server(self) -> str:
        return f"{self.server_host}:{self.server_port}"

    @model_validator(mode="after")
    def _post_init_ext_env(self):
        if not self.mineflayer:
            self.mineflayer = SubprocessMonitor(
                commands=[
                    "node",
                    METAGPT_ROOT.joinpath("metagpt", "environment", "minecraft", "mineflayer", "index.js"),
                    str(self.server_port),
                ],
                name="mineflayer",
                ready_match=r"Server started on port (\d+)",
            )
        if not self.warm_up:
            warm_up = MC_DEFAULT_WARMUP
            if "optional_inventory_items" in warm_up:
                assert MC_CORE_INVENTORY_ITEMS is not None
                # self.core_inv_items_regex = re.compile(MC_CORE_INVENTORY_ITEMS)
                self.warm_up["optional_inventory_items"] = warm_up["optional_inventory_items"]
            else:
                self.warm_up["optional_inventory_items"] = 0
            for key in MC_CURRICULUM_OB:
                self.warm_up[key] = warm_up.get(key, MC_DEFAULT_WARMUP[key])
            self.warm_up["nearby_blocks"] = 0
            self.warm_up["inventory"] = 0
            self.warm_up["completed_tasks"] = 0
            self.warm_up["failed_tasks"] = 0

        # init ckpt sub-forders
        MC_CKPT_DIR.joinpath("curriculum/vectordb").mkdir(parents=True, exist_ok=True)
        MC_CKPT_DIR.joinpath("action").mkdir(exist_ok=True)
        MC_CKPT_DIR.joinpath("skill/code").mkdir(parents=True, exist_ok=True)
        MC_CKPT_DIR.joinpath("skill/description").mkdir(exist_ok=True)
        MC_CKPT_DIR.joinpath("skill/vectordb").mkdir(exist_ok=True)

    def set_mc_port(self, mc_port: int):
        self.mc_port = mc_port

    @mark_as_writeable
    def close(self) -> bool:
        self.unpause()
        if self.connected:
            res = requests.post(f"{self.server}/stop")
            if res.status_code == 200:
                self.connected = False
        self.mineflayer.stop()
        return not self.connected

    @mark_as_writeable
    def check_process(self) -> dict:
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
                logger.error(f"Minecraft server reply with code {res.status_code}")
                raise {}
            return res.json()

    @mark_as_writeable
    def _reset(self, *, seed=None, options=None) -> dict:
        if options is None:
            options = {}
        if options.get("inventory", {}) and options.get("mode", "hard") != "hard":
            logger.error("inventory can only be set when options is hard")
            raise {}

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

    @mark_as_writeable
    def _step(self, code: str, programs: str = "") -> dict:
        if not self.has_reset:
            raise RuntimeError("Environment has not been reset yet")
        self.check_process()
        self.unpause()
        data = {
            "code": code,
            "programs": programs,
        }
        res = requests.post(f"{self.server}/step", json=data, timeout=self.request_timeout)
        if res.status_code != 200:
            raise RuntimeError("Failed to step Minecraft server")
        returned_data = res.json()
        self.pause()
        return json.loads(returned_data)

    @mark_as_writeable
    def pause(self) -> bool:
        if self.mineflayer.is_running and not self.server_paused:
            res = requests.post(f"{self.server}/pause")
            if res.status_code == 200:
                self.server_paused = True
        return self.server_paused

    @mark_as_writeable
    def unpause(self) -> bool:
        if self.mineflayer.is_running and self.server_paused:
            res = requests.post(f"{self.server}/pause")
            if res.status_code == 200:
                self.server_paused = False
            else:
                logger.info(f"mineflayer pause result: {res.json()}")
        return self.server_paused
