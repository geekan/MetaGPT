#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : manual record user interaction in stage=learn & mode=manual, LIKE scripts/step_recorder.py
import time
from pathlib import Path

import cv2

from examples.andriod_assistant.utils.schema import (
    ActionOp,
    AndroidActionOutput,
    AndroidElement,
    RunState,
    SwipeOp
)
from examples.andriod_assistant.utils.utils import draw_bbox_multi, traverse_xml_tree
from metagpt.actions.action import Action
from metagpt.config2 import config
from metagpt.const import ADB_EXEC_FAIL
from metagpt.environment.android_env.android_env import AndroidEnv
from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.logs import logger


class ManualRecord(Action):
    """do a human operation on the screen with human input"""
    name: str = "ManualRecord"

    useless_list: list[str] = []  # store useless elements uid
    record_path: Path = ""
    task_desc_path: Path = ""
    screenshot_before_path: Path = ""
    screenshot_after_path: Path = ""
    xml_path: Path = ""

    # async def run(self, demo_name: str, task_desc: str,task_dir: Path, env: AndroidEnv):
    async def run(self, task_desc: str, task_dir: Path, env: AndroidEnv):

        self.record_path = Path(task_dir) / "record.txt"
        self.task_desc_path = Path(task_dir) / "task_desc.txt"
        self.screenshot_before_path = Path(task_dir)/"raw_screenshots"
        self.screenshot_after_path = Path(task_dir)/"labeled_screenshots"
        self.xml_path =  Path(task_dir)/"xml"

        for path in [self.screenshot_before_path,self.screenshot_after_path, self.xml_path]:
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)

        with open(self.record_path, 'w') as file:
            file.write('')
        record_file = open(self.record_path, "w")
        with open(self.task_desc_path, "w") as f:
            f.write(task_desc)
        step = 0
        while True:
            step += 1
            screenshot_path: Path = await env.observe(
                EnvAPIAbstract(
                    api_name="get_screenshot",
                    # kwargs={"ss_name": f"{demo_name}_{step}", "local_save_dir": self.screenshot_before_path}
                    kwargs={"ss_name": f"{step}", "local_save_dir": self.screenshot_before_path}
                )
            )
            xml_path: Path = await env.observe(
                EnvAPIAbstract(
                    api_name="get_xml",
                    # kwargs={"xml_name": f"{demo_name}_{step}", "local_save_dir": self.xml_path}
                    kwargs={"xml_name": f"{step}", "local_save_dir": self.xml_path}
                )
            )
            if not screenshot_path.exists() or not xml_path.exists():
                return AndroidActionOutput(action_state=RunState.FAIL)
            clickable_list = []
            focusable_list = []
            traverse_xml_tree(xml_path, clickable_list, "clickable", True)
            traverse_xml_tree(xml_path, focusable_list, "focusable", True)
            elem_list = []
            for elem in clickable_list:
                if elem.uid in self.useless_list:
                    continue
                elem_list.append(elem)
            for elem in focusable_list:
                if elem.uid in self.useless_list:
                    continue
                bbox = elem.bbox
                center = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
                close = False
                for e in clickable_list:
                    bbox = e.bbox
                    center_ = (bbox[0][0] + bbox[1][0]) // 2, (bbox[0][1] + bbox[1][1]) // 2
                    dist = (abs(center[0] - center_[0]) ** 2 + abs(center[1] - center_[1]) ** 2) ** 0.5
                    if dist <= config.get_other("min_dist"):
                        close = True
                        break
                if not close:
                    elem_list.append(elem)
            screenshot_labeled_path = Path(self.screenshot_after_path).joinpath(f"{step}_labeled.png")
            # screenshot_labeled_path = Path(self.screenshot_after_path).joinpath(f"{demo_name}_{step}_labeled.png")
            labeled_img = draw_bbox_multi(screenshot_path, screenshot_labeled_path, elem_list)

            cv2.imshow("image", labeled_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            user_input = "xxx"
            logger.info(
                "Choose one of the following actions you want to perform on the current screen:\ntap, text, long_press,"
                "swipe, stop",
                "blue",
            )

            while (
                    user_input.lower() != ActionOp.TAP.value
                    and user_input.lower() != ActionOp.TEXT.value
                    and user_input.lower() != ActionOp.LONG_PRESS.value
                    and user_input.lower() != ActionOp.SWIPE.value
                    and user_input.lower() != ActionOp.STOP.value
            ):
                user_input = input()

            if user_input.lower() == ActionOp.TAP.value:
                logger.info(
                    f"Which element do you want to tap? Choose a numeric tag from 1 to {len(elem_list)}:", "blue"
                )
                user_input = "xxx"
                while not user_input.isnumeric() or int(user_input) > len(elem_list) or int(user_input) < 1:
                    user_input = input()
                tl, br = elem_list[int(user_input) - 1].bbox
                x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                ret = await env.step(EnvAPIAbstract(api_name="system_tap", kwargs={"x": x, "y": y}))
                if ret == ADB_EXEC_FAIL:
                    return AndroidActionOutput(action_state=RunState.FAIL)
                record_file.write(f"tap({int(user_input)}):::{elem_list[int(user_input) - 1].uid}\n")
            elif user_input.lower() == ActionOp.TEXT.value:
                logger.info(
                    f"Which element do you want to input the text string? Choose a numeric tag from 1 to "
                    f"{len(elem_list)}:",
                    "blue",
                )
                input_area = "xxx"
                while not input_area.isnumeric() or int(input_area) > len(elem_list) or int(input_area) < 1:
                    input_area = input()
                logger.info("Enter your input text below:", "blue")
                user_input = ""
                while not user_input:
                    user_input = input()
                await env.step(EnvAPIAbstract(api_name="user_input", kwargs={"input_txt": user_input}))
                record_file.write(f'text({input_area}:sep:"{user_input}"):::{elem_list[int(input_area) - 1].uid}\n')
            elif user_input.lower() == ActionOp.LONG_PRESS.value:
                logger.info(
                    f"Which element do you want to long press? Choose a numeric tag from 1 to {len(elem_list)}:", "blue"
                )
                user_input = "xxx"
                while not user_input.isnumeric() or int(user_input) > len(elem_list) or int(user_input) < 1:
                    user_input = input()
                tl, br = elem_list[int(user_input) - 1].bbox
                x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                ret = await env.step(EnvAPIAbstract(api_name="user_longpress", kwargs={"x": x, "y": y}))
                if ret == ADB_EXEC_FAIL:
                    return AndroidActionOutput(action_state=RunState.FAIL)
                record_file.write(f"long_press({int(user_input)}):::{elem_list[int(user_input) - 1].uid}\n")
            elif user_input.lower() == ActionOp.SWIPE.value:
                logger.info(
                    "What is the direction of your swipe? Choose one from the following options:\nup, down, left,"
                    " right",
                    "blue",
                )
                user_input = ""
                while (
                        user_input != SwipeOp.UP.value
                        and user_input != SwipeOp.DOWN.value
                        and user_input != SwipeOp.LEFT.value
                        and user_input != SwipeOp.RIGHT.value
                ):
                    user_input = input()
                swipe_dir = user_input
                logger.info(f"Which element do you want to swipe? Choose a numeric tag from 1 to {len(elem_list)}:")
                while not user_input.isnumeric() or int(user_input) > len(elem_list) or int(user_input) < 1:
                    user_input = input()
                tl, br = elem_list[int(user_input) - 1].bbox
                x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                ret = await env.step(EnvAPIAbstract(api_name="user_swipe", kwargs={"x": x, "y": y, "orient": swipe_dir}))
                if ret == ADB_EXEC_FAIL:
                    return AndroidActionOutput(action_state=RunState.FAIL)
                record_file.write(f"swipe({int(user_input)}:sep:{swipe_dir}):::{elem_list[int(user_input) - 1].uid}\n")
            elif user_input.lower() == ActionOp.STOP.value:
                record_file.write("stop\n")
                record_file.close()
                break
            else:
                break
            time.sleep(3)


