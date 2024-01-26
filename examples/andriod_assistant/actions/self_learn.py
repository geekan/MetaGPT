#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/self_explorer.py in stage=learn & mode=auto self_explore_task stage

from pathlib import Path

from examples.andriod_assistant.actions.screenshot_parse_an import SCREENSHOT_PARSE_NODE
from examples.andriod_assistant.prompts.assistant_prompt import (
    screenshot_parse_self_explore_template,
)
from examples.andriod_assistant.utils.utils import draw_bbox_multi, traverse_xml_tree
from metagpt.actions.action import Action
from metagpt.config2 import config
from metagpt.environment.android_env.android_env import AndroidEnv
from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.utils.common import encode_image


class SelfLearn(Action):
    name: str = "SelfLearn"

    useless_list: list[str] = []  # store useless elements uid

    async def run(self, round_count: int, task_desc: str, last_act: str, task_dir: Path, env: AndroidEnv):
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
        draw_bbox_multi(screenshot_path, task_dir.joinpath(f"{round_count}_before_labeled.png"), elem_list)
        encode_image(task_dir.joinpath(f"{round_count}_before_labeled.png"))

        self_explore_template = screenshot_parse_self_explore_template
        context = self_explore_template.format(task_description=task_desc, last_act=last_act)

        await SCREENSHOT_PARSE_NODE.fill(context=context, llm=self.llm)
