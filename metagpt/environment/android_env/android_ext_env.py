#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : The Android external environment to integrate with Android apps

import subprocess
from pathlib import Path
from typing import Any, Optional

from pydantic import Field

from metagpt.environment.android_env.const import ADB_EXEC_FAIL
from metagpt.environment.base_env import ExtEnv, mark_as_readable, mark_as_writeable


class AndroidExtEnv(ExtEnv):
    device_id: Optional[str] = Field(default=None)
    screenshot_dir: Optional[Path] = Field(default=None)
    xml_dir: Optional[Path] = Field(default=None)
    width: int = Field(default=720, description="device screen width")
    height: int = Field(default=1080, description="device screen height")

    def __init__(self, **data: Any):
        super().__init__(**data)
        if data.get("device_id"):
            (width, height) = self.device_shape
            self.width = data.get("width", width)
            self.height = data.get("height", height)

    @property
    def adb_prefix_si(self):
        """adb cmd prefix with `device_id` and `shell input`"""
        return f"adb -s {self.device_id} shell input "

    @property
    def adb_prefix_shell(self):
        """adb cmd prefix with `device_id` and `shell`"""
        return f"adb -s {self.device_id} shell "

    @property
    def adb_prefix(self):
        """adb cmd prefix with `device_id`"""
        return f"adb -s {self.device_id} "

    def execute_adb_with_cmd(self, adb_cmd: str) -> str:
        res = subprocess.run(adb_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        exec_res = ADB_EXEC_FAIL
        if not res.returncode:
            exec_res = res.stdout.strip()
        return exec_res

    @property
    def device_shape(self) -> tuple[int, int]:
        adb_cmd = f"{self.adb_prefix_shell} wm size"
        shape = (0, 0)
        shape_res = self.execute_adb_with_cmd(adb_cmd)
        if shape_res != ADB_EXEC_FAIL:
            shape = tuple(map(int, shape_res.split(": ")[1].split("x")))
        return shape

    def list_devices(self):
        adb_cmd = "adb devices"
        res = self.execute_adb_with_cmd(adb_cmd)
        devices = []
        if res != ADB_EXEC_FAIL:
            devices = res.split("\n")[1:]
            devices = [device.split()[0] for device in devices]
        return devices

    @mark_as_readable
    def get_screenshot(self, ss_name: str, local_save_dir: Path) -> Path:
        """
        ss_name: screenshot file name
        local_save_dir: local dir to store image from virtual machine
        """
        assert self.screenshot_dir
        ss_remote_path = Path(self.screenshot_dir).joinpath(f"{ss_name}.png")
        ss_cmd = f"{self.adb_prefix_shell} screencap -p {ss_remote_path}"
        ss_res = self.execute_adb_with_cmd(ss_cmd)

        res = ADB_EXEC_FAIL
        if ss_res != ADB_EXEC_FAIL:
            ss_local_path = Path(local_save_dir).joinpath(f"{ss_name}.png")
            pull_cmd = f"{self.adb_prefix} pull {ss_remote_path} {ss_local_path}"
            pull_res = self.execute_adb_with_cmd(pull_cmd)
            if pull_res != ADB_EXEC_FAIL:
                res = ss_local_path
        return Path(res)

    @mark_as_readable
    def get_xml(self, xml_name: str, local_save_dir: Path) -> Path:
        xml_remote_path = Path(self.xml_dir).joinpath(f"{xml_name}.xml")
        dump_cmd = f"{self.adb_prefix_shell} uiautomator dump {xml_remote_path}"
        xml_res = self.execute_adb_with_cmd(dump_cmd)

        res = ADB_EXEC_FAIL
        if xml_res != ADB_EXEC_FAIL:
            xml_local_path = Path(local_save_dir).joinpath(f"{xml_name}.xml")
            pull_cmd = f"{self.adb_prefix} pull {xml_remote_path} {xml_local_path}"
            pull_res = self.execute_adb_with_cmd(pull_cmd)
            if pull_res != ADB_EXEC_FAIL:
                res = xml_local_path
        return Path(res)

    @mark_as_writeable
    def system_back(self) -> str:
        adb_cmd = f"{self.adb_prefix_si} keyevent KEYCODE_BACK"
        back_res = self.execute_adb_with_cmd(adb_cmd)
        return back_res

    @mark_as_writeable
    def system_tap(self, x: int, y: int) -> str:
        adb_cmd = f"{self.adb_prefix_si} tap {x} {y}"
        tap_res = self.execute_adb_with_cmd(adb_cmd)
        return tap_res

    @mark_as_writeable
    def user_input(self, input_txt: str) -> str:
        input_txt = input_txt.replace(" ", "%s").replace("'", "")
        adb_cmd = f"{self.adb_prefix_si} text {input_txt}"
        input_res = self.execute_adb_with_cmd(adb_cmd)
        return input_res

    @mark_as_writeable
    def user_longpress(self, x: int, y: int, duration: int = 500) -> str:
        adb_cmd = f"{self.adb_prefix_si} swipe {x} {y} {x} {y} {duration}"
        press_res = self.execute_adb_with_cmd(adb_cmd)
        return press_res

    @mark_as_writeable
    def user_swipe(self, x: int, y: int, orient: str = "up", dist: str = "medium", if_quick: bool = False) -> str:
        dist_unit = int(self.width / 10)
        if dist == "long":
            dist_unit *= 3
        elif dist == "medium":
            dist_unit *= 2

        if orient == "up":
            offset = 0, -2 * dist_unit
        elif orient == "down":
            offset = 0, 2 * dist_unit
        elif orient == "left":
            offset = -1 * dist_unit, 0
        elif orient == "right":
            offset = dist_unit, 0
        else:
            return ADB_EXEC_FAIL

        duration = 100 if if_quick else 400
        adb_cmd = f"{self.adb_prefix_si} swipe {x} {y} {x + offset[0]} {y + offset[1]} {duration}"
        swipe_res = self.execute_adb_with_cmd(adb_cmd)
        return swipe_res

    @mark_as_writeable
    def user_swipe_to(self, start: tuple[int, int], end: tuple[int, int], duration: int = 400):
        adb_cmd = f"{self.adb_prefix_si} swipe {start[0]} {start[1]} {end[0]} {end[1]} {duration}"
        swipe_res = self.execute_adb_with_cmd(adb_cmd)
        return swipe_res
