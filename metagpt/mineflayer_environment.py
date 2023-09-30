# -*- coding: utf-8 -*-
# @Date    : 2023/09/25 22:13
# @Author  : yuymf
# @Desc    : @https://github.com/MineDojo/Voyager/blob/main/voyager/env/bridge.py
import os
import time
import json
import requests
import re

from metagpt.logs import logger
import metagpt.utils.minecraft as U
from metagpt.utils.minecraft.process_monitor import SubprocessMonitor
from metagpt.const import CKPT_DIR, DEFAULT_WARMUP, CURRICULUM_OB, CORE_INVENTORY_ITEMS

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

        self.warm_up = {} # turns that when to add part of curriculum_ob to HumanMessage TODO: MV
        self.core_inv_items_regex = None

        self._set_warmup()

        os.makedirs(f"{CKPT_DIR}/curriculum/vectordb", exist_ok=True)
        os.makedirs(f"{CKPT_DIR}/action", exist_ok=True)

    def _set_warmup(self):
        warm_up = DEFAULT_WARMUP
        if "optional_inventory_items" in warm_up:
            assert CORE_INVENTORY_ITEMS is not None
            self.core_inv_items_regex = re.compile(
                CORE_INVENTORY_ITEMS
            )
            self.warm_up["optional_inventory_items"] = warm_up[
                "optional_inventory_items"
            ]
        else:
            self.warm_up["optional_inventory_items"] = 0
        for key in CURRICULUM_OB:
            self.warm_up[key] = warm_up.get(key, DEFAULT_WARMUP[key])
        self.warm_up["nearby_blocks"] = 0
        self.warm_up["inventory"] = 0
        self.warm_up["completed_tasks"] = 0
        self.warm_up["failed_tasks"] = 0

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
                logger.error(f"Minecraft server reply with code {res.status_code}")
                raise {}
            return res.json()

    def reset(
        self,
        *,
        seed=None,
        options=None,
    ):
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
