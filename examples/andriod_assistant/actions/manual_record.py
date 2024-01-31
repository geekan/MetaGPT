#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : manual record user interaction in stage=learn & mode=manual, LIKE scripts/step_recorder.py
import time
from pathlib import Path

import cv2

from examples.andriod_assistant.utils.schema import (
    ActionOp,
    AndroidElement,
    SwipeOp,
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

    async def run(self, demo_name: str, task_dir: Path, env: AndroidEnv):
        # Question 这里是将通过ADB获取的东西存到本地的路径的吧
        screenshot_path: Path = env.step(
            EnvAPIAbstract(api_name="get_screenshot", kwargs={"ss_name": f"{demo_name}", "local_save_dir": task_dir})
        )
        xml_path: Path = env.step(
            EnvAPIAbstract(api_name="get_xml", kwargs={"xml_name": f"{demo_name}", "local_save_dir": task_dir})
        )
        if not screenshot_path.exists() or not xml_path.exists():
            # TODO exit
            return
        step = 0
        record_path = Path(task_dir) / "record.txt"
        record_file = open(record_path, "w")
        while True:
            # TODO Parse Record Step 是否可以从这个函数中获取，进行参数的传递 ？
            step += 1
            clickable_list = []
            focusable_list = []
            traverse_xml_tree(xml_path, clickable_list, "clickable", True)
            traverse_xml_tree(xml_path, focusable_list, "focusable", True)
            elem_list: list[AndroidElement] = clickable_list.copy()

            for elem in focusable_list:
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
            screenshot_labeled_path = task_dir.joinpath(f"{task_dir}_{step}_labeled.png")
            labeled_img = draw_bbox_multi(screenshot_path, screenshot_labeled_path, elem_list)

            cv2.imshow("image", labeled_img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()

            user_input = "xxx"
            logger.info(
                "Choose one of the following actions you want to perform on the current screen:\ntap, text, long "
                "press, swipe, stop",
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
                ret = env.step(EnvAPIAbstract(api_name="user_tap", kwargs={"x": x, "y": y}))
                # Question 将 ERROR 替换为 ADB_EXEC_FAIL(FAILED)
                if ret == ADB_EXEC_FAIL:
                    logger.info("ERROR: tap execution failed", "red")
                    break
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
                env.step(EnvAPIAbstract(api_name="user_input", kwargs={"input_txt": user_input}))
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
                env.step(EnvAPIAbstract(api_name="user_longpress", kwargs={"x": x, "y": y}))
                if ret == ADB_EXEC_FAIL:
                    logger.info("ERROR: long press execution failed", "red")
                    break
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
                ret = env.step(EnvAPIAbstract("user_swipe", kwargs={"x": x, "y": y, "orient": swipe_dir}))
                if ret == ADB_EXEC_FAIL:
                    logger.info("ERROR: swipe execution failed", "red")
                    break
                record_file.write(f"swipe({int(user_input)}:sep:{swipe_dir}):::{elem_list[int(user_input) - 1].uid}\n")
            elif user_input.lower() == ActionOp.STOP.value:
                record_file.write("stop\n")
                record_file.close()
                break
            else:
                break
            time.sleep(3)
