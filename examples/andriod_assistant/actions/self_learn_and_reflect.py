#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/self_explorer.py in stage=learn & mode=auto self_explore_task stage

from pathlib import Path
import ast

from examples.andriod_assistant.actions.screenshot_parse_an import SCREENSHOT_PARSE_NODE
from examples.andriod_assistant.actions.self_learn_reflect_an import SELF_LEARN_REFLECT_NODE
from examples.andriod_assistant.prompts.assistant_prompt import (
    screenshot_parse_self_explore_template, screenshot_parse_self_explore_reflect_template as reflect_template
)
from examples.andriod_assistant.utils.schema import AndroidElement, OpLogItem, ReflectLogItem, ParamExtState, TapOp, TextOp, SwipeOp, LongPressOp, ActionOp, Decision, DocContent
from examples.andriod_assistant.utils.utils import draw_bbox_multi, traverse_xml_tree, screenshot_parse_extract, elem_bbox_to_xy, reflect_parse_extarct
from metagpt.actions.action import Action
from metagpt.config2 import config
from metagpt.environment.android_env.android_env import AndroidEnv
from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.utils.common import encode_image
from metagpt.const import ADB_EXEC_FAIL
from metagpt.logs import logger


class SelfLearnAndReflect(Action):
    name: str = "SelfLearnAndReflect"

    useless_list: list[str] = []  # store useless elements uid

    screenshot_before_path: str = ""
    screenshot_before_base64: str = ""
    elem_list: list[AndroidElement] = []
    swipe_orient: str = "up"
    act_name: str = ""
    ui_area: int = -1

    async def run(self, round_count: int, task_desc: str, last_act: str, task_dir: Path, docs_dir: Path, env: AndroidEnv):
        self.run_self_learn(round_count, task_desc, last_act, task_dir, env)
        self.run_reflect(round_count, task_desc, last_act, task_dir, docs_dir, env)

    async def run_self_learn(self, round_count: int, task_desc: str, last_act: str, task_dir: Path, env: AndroidEnv):
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
        screenshot_before_labeled_path = task_dir.joinpath(f"{round_count}_before_labeled.png")
        draw_bbox_multi(screenshot_path, screenshot_before_labeled_path, elem_list)
        img_base64 = encode_image(screenshot_before_labeled_path)
        self.screenshot_before_base64 = img_base64
        self.screenshot_before_path = screenshot_before_labeled_path

        self_explore_template = screenshot_parse_self_explore_template
        context = self_explore_template.format(task_description=task_desc, last_act=last_act)

        node = await SCREENSHOT_PARSE_NODE.fill(context=context, llm=self.llm, images=[img_base64])
        if "error" in node.content:
            # TODO
            return
        prompt = node.compile(context=context, schema="json", mode="auto")
        log_item = OpLogItem(step=round_count, prompt=prompt, image=screenshot_before_labeled_path, response=node.content)
        op_param = screenshot_parse_extract(node.instruct_content.model_dump(), grid_on=False)
        if op_param.param_state == ParamExtState.FINISH:
            # TODO
            return
        if op_param.param_state == ParamExtState.FAIL:
            # TODO
            return

        if isinstance(op_param, TapOp):
            self.ui_area = op_param.area
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
            self.ui_area = op_param.area
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            res = env.step(EnvAPIAbstract("user_longpress", kwargs={"x": x, "y": y}))
            if res == ADB_EXEC_FAIL:
                # TODO
                return
        elif isinstance(op_param, SwipeOp):
            self.ui_area = op_param.area
            self.swipe_orient = op_param.swipe_orient
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            res = env.step(EnvAPIAbstract("user_swipe", kwargs={"x": x, "y": y, "orient": op_param.swipe_orient, "dist": op_param.dist}))
            if res == ADB_EXEC_FAIL:
                # TODO
                return

        self.elem_list = elem_list
        self.act_name = op_param.act_name

    async def run_reflect(self, round_count: int, task_desc: str, last_act: str, task_dir: Path, docs_dir: Path, env: AndroidEnv):
        screenshot_path: Path = env.step(
            EnvAPIAbstract(
                api_name="get_screenshot", kwargs={"ss_name": f"{round_count}_after", "local_save_dir": task_dir}
            )
        )
        if not screenshot_path.exists():
            # TODO
            return

        screenshot_after_labeled_path = task_dir.joinpath(f"{round_count}_after_labeled.png")
        draw_bbox_multi(screenshot_path, screenshot_after_labeled_path, elem_list=self.elem_list)
        img_base64 = encode_image(screenshot_after_labeled_path)

        if self.act_name == ActionOp.TAP.value:
            action = "tapping"
        elif self.act_name == ActionOp.LONG_PRESS.value:
            action = "long pressing"
        elif self.act_name == ActionOp.SWIPE.value:
            action = "swiping"
            if self.swipe_orient == SwipeOp.UP.value or self.swipe_orient == SwipeOp.DOWN.value:
                action = "v_swipe"
            elif self.swipe_orient == SwipeOp.LEFT.value or self.swipe_orient == SwipeOp.RIGHT.value:
                action = "h_swipe"
        context = reflect_template.format(action=action, ui_element=str(self.ui_area), task_desc=task_desc, last_act=last_act)
        node = await SELF_LEARN_REFLECT_NODE.fill(context=context, llm=self.llm, images=[self.screenshot_before_base64, img_base64])

        if "error" in node.content:
            # TODO
            return

        prompt = node.compile(context=context, schema="json", mode="auto")
        log_item = ReflectLogItem(step=round_count, prompt=prompt, image_before=self.screenshot_before_path,
                                  image_after=screenshot_after_labeled_path, response=node.content)

        op_param = reflect_parse_extarct(node.instruct_content.model_dump())
        if op_param.param_state == ParamExtState.FINISH:
            # TODO
            return
        if op_param.param_state == ParamExtState.FAIL:
            # TODO
            return

        resource_id = self.elem_list[int(self.ui_area) -1].uid
        if op_param.decision == Decision.INEFFECTIVE.value:
            self.useless_list.append(resource_id)
            last_act = "NONE"  # TODO global
        elif op_param.decision in [Decision.BACK.value, Decision.CONTINUE.value, Decision.SUCCESS.value]:
            if op_param.decision in [Decision.BACK.value, Decision.CONTINUE.value]:
                self.useless_list.append(resource_id)
                last_act = "NONE"
                if op_param.decision == Decision.BACK.value:
                    res = env.step(EnvAPIAbstract("system_back"))
                    if res == ADB_EXEC_FAIL:
                        # TODO
                        return
            doc = op_param.documentation
            doc_path = docs_dir.joinpath(f"{resource_id}.txt")
            if doc_path.exists():
                doc_content = ast.literal_eval(open(doc_path).read())
                if doc_content[self.act_name]:
                    logger.info(f"Documentation for the element {resource_id} already exists.")
                    # TODO
                    return
            else:
                doc_content = DocContent()
                setattr(doc_content, self.act_name, doc)
            doc_path.write_text(str(doc_content))
