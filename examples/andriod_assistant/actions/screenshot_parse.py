#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/task_executor.py in stage=act

from pathlib import Path

from examples.andriod_assistant.prompts.assistant_prompt import (
    screenshot_parse_template,
    screenshot_parse_with_grid_template,
)
from examples.andriod_assistant.utils.utils import draw_bbox_multi, traverse_xml_tree
from metagpt.actions.action import Action
from metagpt.config2 import config
from metagpt.environment.android_env.android_env import AndroidEnv
from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.utils.common import encode_image


class ScreenshotParse(Action):
    name: str = "ScreenshotParse"

    async def run(
        self, round_count: int, task_desc: str, last_act: str, task_dir: Path, env: AndroidEnv, grid_on: bool = False
    ):
        screenshot_path: Path = env.step(
            EnvAPIAbstract(
                api_name="get_screenshot", kwargs={"ss_name": f"{round_count}_before", "local_save_dir": task_dir}
            )
        )
        xml_path: Path = env.step(
            EnvAPIAbstract(api_name="get_xml", kwargs={"xml_name": f"{round_count}", "local_save_dir": task_dir})
        )
        if not screenshot_path.exists() or not xml_path.exists():
            # TODO exit
            return

        clickable_list = []
        focusable_list = []
        traverse_xml_tree(xml_path, clickable_list, "clickable", True)
        traverse_xml_tree(xml_path, focusable_list, "focusable", True)
        elem_list = clickable_list.copy()
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
        draw_bbox_multi(screenshot_path, task_dir.joinpath(f"{task_dir}_{round_count}_labeled.png"), elem_list)
        encode_image(task_dir.joinpath(f"{task_dir}_{round_count}_labeled.png"))

        parse_template = screenshot_parse_with_grid_template if grid_on else screenshot_parse_template

        # makeup `ui_doc`
        # TODO
        ui_doc = ""

        parse_template.format(ui_document=ui_doc, task_description=task_desc, last_act=last_act)
