#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/self_explorer.py  self_explore_reflect stage

from pathlib import Path

from examples.andriod_assistant.prompts.assistant_prompt import (
    screenshot_parse_self_explore_reflect_template,
)
from examples.andriod_assistant.utils.schema import AndroidElement
from examples.andriod_assistant.utils.utils import draw_bbox_multi
from metagpt.actions.action import Action
from metagpt.environment.android_env.android_env import AndroidEnv
from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.utils.common import encode_image


class SelfLearnReflect(Action):
    name: str = "SelfLearnReflect"

    async def run(
        self,
        round_count: int,
        task_desc: str,
        last_act: str,
        task_dir: Path,
        env: AndroidEnv,
        elem_list: list[AndroidElement],
        act_name: str,
        swipe_dir: str,
        ui_area: int,
    ):
        if act_name == "text":
            # TODO ignore current reflect
            return

        screenshot_path: Path = env.step(
            EnvAPIAbstract(
                api_name="get_screenshot", kwargs={"ss_name": f"{round_count}_before", "local_save_dir": task_dir}
            )
        )
        if not screenshot_path.exists():
            # TODO exit
            return

        draw_bbox_multi(screenshot_path, task_dir.joinpath(f"{round_count}_after_labeled.png"), elem_list)
        encode_image(task_dir.joinpath(f"{round_count}_after_labeled.png"))

        reflect_template = screenshot_parse_self_explore_reflect_template
        if act_name == "tap":
            action = "tapping"
        elif act_name == "long_press":
            action = "long pressing"
        elif act_name == "swipe":
            action = "swiping"
            if swipe_dir == "up" or swipe_dir == "down":
                action = "v_swipe"
            elif swipe_dir == "left" or swipe_dir == "right":
                action = "h_swipe"

        reflect_template.format(action=action, ui_element=str(ui_area), task_desc=task_desc, last_act=last_act)
