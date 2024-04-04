#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : manual record user interaction in stage=learn & mode=manual, LIKE scripts/step_recorder.py
import time
from pathlib import Path

import cv2

from metagpt.actions.action import Action
from metagpt.config2 import config
from metagpt.environment.android.android_env import AndroidEnv
from metagpt.environment.android.const import ADB_EXEC_FAIL
from metagpt.environment.android.env_space import (
    EnvAction,
    EnvActionType,
    EnvObsParams,
    EnvObsType,
)
from metagpt.ext.android_assistant.utils.schema import (
    ActionOp,
    AndroidActionOutput,
    RunState,
    SwipeOp,
)
from metagpt.ext.android_assistant.utils.utils import (
    draw_bbox_multi,
    elem_list_from_xml_tree,
)
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

    async def run(self, task_desc: str, task_dir: Path, env: AndroidEnv):
        self.record_path = Path(task_dir) / "record.txt"
        self.task_desc_path = Path(task_dir) / "task_desc.txt"
        self.screenshot_before_path = Path(task_dir) / "raw_screenshots"
        self.screenshot_after_path = Path(task_dir) / "labeled_screenshots"
        self.xml_path = Path(task_dir) / "xml"
        for path in [self.screenshot_before_path, self.screenshot_after_path, self.xml_path]:
            path.mkdir(parents=True, exist_ok=True)

        self.record_path.write_text("")
        record_file = open(self.record_path, "w")
        self.task_desc_path.write_text(task_desc)

        step = 0
        extra_config = config.extra
        while True:
            step += 1
            screenshot_path: Path = env.observe(
                EnvObsParams(
                    obs_type=EnvObsType.GET_SCREENSHOT, ss_name=f"{step}", local_save_dir=self.screenshot_before_path
                )
            )
            xml_path: Path = env.observe(
                EnvObsParams(obs_type=EnvObsType.GET_XML, xml_name=f"{step}", local_save_dir=self.xml_path)
            )
            if not screenshot_path.exists() or not xml_path.exists():
                return AndroidActionOutput(action_state=RunState.FAIL)

            elem_list = elem_list_from_xml_tree(xml_path, self.useless_list, extra_config.get("min_dist", 30))

            screenshot_labeled_path = Path(self.screenshot_after_path).joinpath(f"{step}_labeled.png")
            labeled_img = draw_bbox_multi(screenshot_path, screenshot_labeled_path, elem_list)

            cv2.namedWindow("image", cv2.WINDOW_NORMAL)
            cv2.imshow("image", labeled_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            user_input = "xxx"
            logger.info(
                "Choose one of the following actions you want to perform on the current screen:\n"
                "tap, text, long_press, swipe, stop"
            )

            while (
                user_input.lower() != ActionOp.TAP.value
                and user_input.lower() != ActionOp.TEXT.value
                and user_input.lower() != ActionOp.LONG_PRESS.value
                and user_input.lower() != ActionOp.SWIPE.value
                and user_input.lower() != ActionOp.STOP.value
            ):
                user_input = input("user_input: ")

            if user_input.lower() == ActionOp.TAP.value:
                logger.info(f"Which element do you want to tap? Choose a numeric tag from 1 to {len(elem_list)}:")
                user_input = "xxx"
                while not user_input.isnumeric() or int(user_input) > len(elem_list) or int(user_input) < 1:
                    user_input = input("user_input: ")
                tl, br = elem_list[int(user_input) - 1].bbox
                x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                action = EnvAction(action_type=EnvActionType.SYSTEM_TAP, coord=(x, y))
                log_str = f"tap({int(user_input)}):::{elem_list[int(user_input) - 1].uid}\n"
            elif user_input.lower() == ActionOp.TEXT.value:
                logger.info(
                    f"Which element do you want to input the text string? Choose a numeric tag from 1 to "
                    f"{len(elem_list)}:"
                )
                input_area = "xxx"
                while not input_area.isnumeric() or int(input_area) > len(elem_list) or int(input_area) < 1:
                    input_area = input("user_input: ")
                logger.info("Enter your input text below:")
                user_input = ""
                while not user_input:
                    user_input = input("user_input: ")
                action = EnvAction(action_type=EnvActionType.USER_INPUT, input_txt=user_input)
                log_str = f"text({input_area}:sep:'{user_input}'):::{elem_list[int(input_area) - 1].uid}\n"
            elif user_input.lower() == ActionOp.LONG_PRESS.value:
                logger.info(
                    f"Which element do you want to long press? Choose a numeric tag from 1 to {len(elem_list)}:"
                )
                user_input = "xxx"
                while not user_input.isnumeric() or int(user_input) > len(elem_list) or int(user_input) < 1:
                    user_input = input("user_input: ")
                tl, br = elem_list[int(user_input) - 1].bbox
                x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2
                action = EnvAction(action_type=EnvActionType.USER_LONGPRESS, coord=(x, y))
                log_str = f"long_press({int(user_input)}):::{elem_list[int(user_input) - 1].uid}\n"
            elif user_input.lower() == ActionOp.SWIPE.value:
                logger.info(
                    "What is the direction of your swipe? Choose one from the following options:\n"
                    "up, down, left, right"
                )
                user_input = ""
                while (
                    user_input != SwipeOp.UP.value
                    and user_input != SwipeOp.DOWN.value
                    and user_input != SwipeOp.LEFT.value
                    and user_input != SwipeOp.RIGHT.value
                ):
                    user_input = input("user_input: ")
                swipe_dir = user_input
                logger.info(f"Which element do you want to swipe? Choose a numeric tag from 1 to {len(elem_list)}:")
                while not user_input.isnumeric() or int(user_input) > len(elem_list) or int(user_input) < 1:
                    user_input = input("user_input: ")
                tl, br = elem_list[int(user_input) - 1].bbox
                x, y = (tl[0] + br[0]) // 2, (tl[1] + br[1]) // 2

                action = EnvAction(action_type=EnvActionType.USER_SWIPE, coord=(x, y), orient=swipe_dir)
                log_str = f"swipe({int(user_input)}:sep:{swipe_dir}):::{elem_list[int(user_input) - 1].uid}\n"
            elif user_input.lower() == ActionOp.STOP.value:
                record_file.write("stop\n")
                record_file.close()
                break
            else:
                break

            obs, _, _, _, info = env.step(action)
            action_res = info["res"]
            if action_res == ADB_EXEC_FAIL:
                return AndroidActionOutput(action_state=RunState.FAIL)
            record_file.write(log_str)

            time.sleep(1)

        return AndroidActionOutput(action_state=RunState.SUCCESS)
