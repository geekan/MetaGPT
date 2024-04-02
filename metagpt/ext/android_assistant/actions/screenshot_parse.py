#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/task_executor.py in stage=act

import ast
from pathlib import Path

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
from metagpt.ext.android_assistant.actions.screenshot_parse_an import (
    SCREENSHOT_PARSE_NODE,
)
from metagpt.ext.android_assistant.prompts.assistant_prompt import (
    screenshot_parse_template,
    screenshot_parse_with_grid_template,
)
from metagpt.ext.android_assistant.utils.schema import (
    AndroidActionOutput,
    AndroidElement,
    GridOpParam,
    LongPressGridOpParam,
    LongPressOpParam,
    OpLogItem,
    RunState,
    SwipeGridOpParam,
    SwipeOpParam,
    TapGridOpParam,
    TapOpParam,
    TextOpParam,
)
from metagpt.ext.android_assistant.utils.utils import (
    area_to_xy,
    draw_bbox_multi,
    draw_grid,
    elem_bbox_to_xy,
    screenshot_parse_extract,
    traverse_xml_tree,
)
from metagpt.logs import logger
from metagpt.utils.common import encode_image


class ScreenshotParse(Action):
    name: str = "ScreenshotParse"

    def _makeup_ui_document(self, elem_list: list[AndroidElement], docs_idr: Path, use_exist_doc: bool = True) -> str:
        if not use_exist_doc:
            return ""

        ui_doc = """
You also have access to the following documentations that describes the functionalities of UI 
elements you can interact on the screen. These docs are crucial for you to determine the target of your 
next action. You should always prioritize these documented elements for interaction: """
        for i, elem in enumerate(elem_list):
            doc_path = docs_idr.joinpath(f"{elem.uid}.txt")
            if not doc_path.exists():
                continue
            try:
                doc_content = ast.literal_eval(doc_path.read_text())
            except Exception as exp:
                logger.error(f"ast parse doc: {doc_path} failed, exp: {exp}")
                continue

            ui_doc += f"Documentation of UI element labeled with the numeric tag '{i + 1}':\n"
            if doc_content["tap"]:
                ui_doc += f"This UI element is clickable. {doc_content['tap']}\n\n"
            if doc_content["text"]:
                ui_doc += (
                    f"This UI element can receive text input. The text input is used for the following "
                    f"purposes: {doc_content['text']}\n\n"
                )
            if doc_content["long_press"]:
                ui_doc += f"This UI element is long clickable. {doc_content['long_press']}\n\n"
            if doc_content["v_swipe"]:
                ui_doc += (
                    f"This element can be swiped directly without tapping. You can swipe vertically on "
                    f"this UI element. {doc_content['v_swipe']}\n\n"
                )
            if doc_content["h_swipe"]:
                ui_doc += (
                    f"This element can be swiped directly without tapping. You can swipe horizontally on "
                    f"this UI element. {doc_content['h_swipe']}\n\n"
                )
        return ui_doc

    async def run(
        self,
        round_count: int,
        task_desc: str,
        last_act: str,
        task_dir: Path,
        docs_dir: Path,
        grid_on: bool,
        env: AndroidEnv,
    ):
        extra_config = config.extra
        for path in [task_dir, docs_dir]:
            path.mkdir(parents=True, exist_ok=True)
        screenshot_path: Path = env.observe(
            EnvObsParams(obs_type=EnvObsType.GET_SCREENSHOT, ss_name=f"{round_count}_before", local_save_dir=task_dir)
        )
        xml_path: Path = env.observe(
            EnvObsParams(obs_type=EnvObsType.GET_XML, xml_name=f"{round_count}", local_save_dir=task_dir)
        )
        if not screenshot_path.exists() or not xml_path.exists():
            return AndroidActionOutput(action_state=RunState.FAIL)

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
                if dist <= extra_config.get("min_dist", 30):
                    close = True
                    break
            if not close:
                elem_list.append(elem)

        screenshot_labeled_path = task_dir.joinpath(f"{round_count}_labeled.png")
        draw_bbox_multi(screenshot_path, screenshot_labeled_path, elem_list)
        img_base64 = encode_image(screenshot_labeled_path)

        parse_template = screenshot_parse_with_grid_template if grid_on else screenshot_parse_template

        if grid_on:
            env.rows, env.cols = draw_grid(screenshot_path, task_dir / f"{round_count}_grid.png")

        ui_doc = self._makeup_ui_document(elem_list, docs_dir)
        context = parse_template.format(ui_document=ui_doc, task_description=task_desc, last_act=last_act)
        node = await SCREENSHOT_PARSE_NODE.fill(context=context, llm=self.llm, images=[img_base64])

        if "error" in node.content:
            return AndroidActionOutput(action_state=RunState.FAIL)

        prompt = node.compile(context=context, schema="json", mode="auto")
        OpLogItem(step=round_count, prompt=prompt, image=str(screenshot_labeled_path), response=node.content)

        op_param = screenshot_parse_extract(node.instruct_content.model_dump(), grid_on)
        if op_param.param_state == RunState.FINISH:
            logger.info(f"op_param: {op_param}")
            return AndroidActionOutput(action_state=RunState.FINISH)
        if op_param.param_state == RunState.FAIL:
            return AndroidActionOutput(action_state=RunState.FAIL)

        last_act = op_param.last_act
        if isinstance(op_param, TapOpParam):
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            action = EnvAction(action_type=EnvActionType.SYSTEM_TAP, coord=(x, y))
        elif isinstance(op_param, TextOpParam):
            action = EnvAction(action_type=EnvActionType.USER_INPUT, input_txt=op_param.input_str)
        elif isinstance(op_param, LongPressOpParam):
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            action = EnvAction(action_type=EnvActionType.USER_LONGPRESS, coord=(x, y))
        elif isinstance(op_param, SwipeOpParam):
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            action = EnvAction(
                action_type=EnvActionType.USER_SWIPE, coord=(x, y), orient=op_param.swipe_orient, dist=op_param.dist
            )
        elif isinstance(op_param, GridOpParam):
            grid_on = True
        elif isinstance(op_param, TapGridOpParam) or isinstance(op_param, LongPressGridOpParam):
            x, y = area_to_xy(op_param.area, op_param.subarea, env.width, env.height, env.rows, env.cols)
            if isinstance(op_param, TapGridOpParam):
                action = EnvAction(action_type=EnvActionType.SYSTEM_TAP, coord=(x, y))
            else:
                # LongPressGridOpParam
                action = EnvAction(action_type=EnvActionType.USER_LONGPRESS, coord=(x, y))
        elif isinstance(op_param, SwipeGridOpParam):
            start_x, start_y = area_to_xy(
                op_param.start_area, op_param.start_subarea, env.width, env.height, env.rows, env.cols
            )
            end_x, end_y = area_to_xy(
                op_param.end_area, op_param.end_subarea, env.width, env.height, env.rows, env.cols
            )
            action = EnvAction(
                action_type=EnvActionType.USER_SWIPE_TO, coord=(start_x, start_y), tgt_coord=(end_x, end_y)
            )

        if not grid_on:
            obs, _, _, _, info = env.step(action)
            action_res = info["res"]
            if action_res == ADB_EXEC_FAIL:
                return AndroidActionOutput(action_state=RunState.FAIL)

        if op_param.act_name != "grid":
            grid_on = False

        return AndroidActionOutput(data={"grid_on": grid_on, "last_act": last_act})
