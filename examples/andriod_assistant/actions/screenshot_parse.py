#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/task_executor.py in stage=act

from pathlib import Path

from examples.andriod_assistant.prompts.assistant_prompt import (
    screenshot_parse_template,
    screenshot_parse_with_grid_template,
)
from examples.andriod_assistant.utils.schema import OpLogItem, ActionOp, ParamExtState, GridOp, ActionOp, TapOp, TapGridOp, \
    LongPressOp, LongPressGridOp, SwipeOp, SwipeGridOp, TextOp, AndroidElement
from examples.andriod_assistant.actions.screenshot_parse_an import SCREENSHOT_PARSE_NODE
from examples.andriod_assistant.utils.utils import draw_bbox_multi, traverse_xml_tree, area_to_xy, screenshot_parse_extract, elem_bbox_to_xy
from metagpt.actions.action import Action
from metagpt.config2 import config
from metagpt.environment.android_env.android_env import AndroidEnv
from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.utils.common import encode_image
from metagpt.const import ADB_EXEC_FAIL


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

        screenshot_labeled_path = task_dir.joinpath(f"{task_dir}_{round_count}_labeled.png")
        draw_bbox_multi(screenshot_path, screenshot_labeled_path, elem_list)
        img_base64 = encode_image(screenshot_labeled_path)

        parse_template = screenshot_parse_with_grid_template if grid_on else screenshot_parse_template

        # makeup `ui_doc`
        # TODO
        ui_doc = ""

        context = parse_template.format(ui_document=ui_doc, task_description=task_desc, last_act=last_act)
        node = await SCREENSHOT_PARSE_NODE.fill(context=context, llm=self.llm, images=[img_base64])

        if "error" in node.content:
            # TODO
            return

        prompt = node.compile(context=context, schema="json", mode="auto")
        log_item = OpLogItem(step=round_count, prompt=prompt, image=screenshot_labeled_path, response=node.content)

        op_param = screenshot_parse_extract(node.instruct_content.model_dump(), grid_on)
        if op_param.param_state == ParamExtState.FINISH:
            # TODO
            return
        if op_param.param_state == ParamExtState.FAIL:
            # TODO
            return

        if isinstance(op_param, TapOp):
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            res = env.step(EnvAPIAbstract("system_tap", kwargs={"x": x, "y": y}))
            if res == ADB_EXEC_FAIL:
                # TODO
                return
        elif isinstance(op_param, TextOp):
            res = env.step(EnvAPIAbstract("user_input", kwargs={"input_txt": op_param.input_str}))
            if res == ADB_EXEC_FAIL:
                # TODO
                return
        elif isinstance(op_param, LongPressOp):
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            res = env.step(EnvAPIAbstract("user_longpress", kwargs={"x": x, "y": y}))
            if res == ADB_EXEC_FAIL:
                # TODO
                return
        elif isinstance(op_param, SwipeOp):
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            res = env.step(EnvAPIAbstract("user_swipe", kwargs={"x": x, "y": y, "orient": op_param.swipe_orient, "dist": op_param.dist}))
            if res == ADB_EXEC_FAIL:
                # TODO
                return
        elif isinstance(op_param, GridOp):
            grid_on = True
        elif isinstance(op_param, TapGridOp) or isinstance(op_param, LongPressGridOp):
            x, y = area_to_xy(op_param.area, op_param.subarea, env.width, env.height, env.rows, env.cols)
            if isinstance(op_param, TapGridOp):
                res = env.step(EnvAPIAbstract("system_tap", kwargs={"x": x, "y": y}))
                if res == ADB_EXEC_FAIL:
                    # TODO
                    return
            else:
                # LongPressGridOp
                res = env.step(EnvAPIAbstract("user_longpress", kwargs={"x": x, "y": y}))
                if res == ADB_EXEC_FAIL:
                    # TODO
                    return
        elif isinstance(op_param, SwipeGridOp):
            start_x, start_y = area_to_xy(op_param.start_area, op_param.start_subarea)
            end_x, end_y = area_to_xy(op_param.end_area, op_param.end_subarea)
            res = env.step(EnvAPIAbstract("user_swipe_to", kwargs={"start": (start_x, start_y), "end": (end_x, end_y)}))
            if res == ADB_EXEC_FAIL:
                # TODO
                return

        if op_param.act_name != "grid":
            grid_on = True  # TODO overwrite it
