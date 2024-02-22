# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/self_explorer.py in stage=learn & mode=auto self_explore_task stage

import ast
from pathlib import Path

from examples.andriod_assistant.actions.screenshot_parse_an import SCREENSHOT_PARSE_NODE
from examples.andriod_assistant.actions.self_learn_reflect_an import (
    SELF_LEARN_REFLECT_NODE,
)
from examples.andriod_assistant.prompts.assistant_prompt import (
    screenshot_parse_self_explore_reflect_template as reflect_template,
)
from examples.andriod_assistant.prompts.assistant_prompt import (
    screenshot_parse_self_explore_template,
)
from examples.andriod_assistant.utils.schema import (
    ActionOp,
    AndroidActionOutput,
    AndroidElement,
    Decision,
    DocContent,
    LongPressOp,
    OpLogItem,
    ReflectLogItem,
    RunState,
    SwipeOp,
    TapOp,
    TextOp,
)
from examples.andriod_assistant.utils.utils import (
    draw_bbox_multi,
    elem_bbox_to_xy,
    reflect_parse_extarct,
    screenshot_parse_extract,
    traverse_xml_tree,
)
from metagpt.actions.action import Action
from metagpt.config2 import config
from metagpt.const import ADB_EXEC_FAIL
from metagpt.environment.android_env.android_env import AndroidEnv
from metagpt.environment.api.env_api import EnvAPIAbstract
from metagpt.logs import logger
from metagpt.utils.common import encode_image


class SelfLearnAndReflect(Action):
    name: str = "SelfLearnAndReflect"

    useless_list: list[str] = []  # store useless elements uid

    screenshot_before_path: str = ""
    screenshot_before_base64: str = ""
    elem_list: list[AndroidElement] = []
    swipe_orient: str = "up"
    act_name: str = ""
    ui_area: int = -1

    async def run(
            self, round_count: int, task_desc: str, last_act: str, task_dir: Path, docs_dir: Path, env: AndroidEnv
    ) -> AndroidActionOutput:
        resp = await self.run_self_learn(round_count, task_desc, last_act, task_dir, env)
        print(resp)
        resp = await self.run_reflect(round_count, task_desc, last_act, task_dir, docs_dir, env)
        print(resp)
        return resp

    async def run_self_learn(
            self, round_count: int, task_desc: str, last_act: str, task_dir: Path, env: AndroidEnv
    ) -> AndroidActionOutput:
        logger.info('run_self_learn')
        screenshot_path: Path = env.observe(
            EnvAPIAbstract(
                api_name="get_screenshot", kwargs={"ss_name": f"{round_count}_before", "local_save_dir": task_dir}
            )
        )
        xml_path: Path = env.observe(
            EnvAPIAbstract(api_name="get_xml", kwargs={"xml_name": f"{round_count}", "local_save_dir": task_dir})
        )
        if not screenshot_path.exists() or not xml_path.exists():
            return AndroidActionOutput(action_state=RunState.FAIL)

        clickable_list = []
        focusable_list = []
        # TODO Tuple Bug 从这里开始 Debug
        # TODO Tuple Bug
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
                # TODO Modify config to default 30. It should be modified back config after single action test
                # if dist <= config.get_other("min_dist"):
                if dist <= 30:
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
        print(f"fill result:{node}")
        if "error" in node.content:
            return AndroidActionOutput(action_state=RunState.FAIL)
        prompt = node.compile(context=context, schema="json", mode="auto")
        # Modify WindowsPath to Str
        OpLogItem(step=round_count, prompt=prompt, image=str(screenshot_before_labeled_path), response=node.content)
        op_param = screenshot_parse_extract(node.instruct_content.model_dump(), grid_on=False)
        if op_param.param_state == RunState.FINISH:
            return AndroidActionOutput(action_state=RunState.FINISH)
        if op_param.param_state == RunState.FAIL:
            return AndroidActionOutput(action_state=RunState.FAIL)

        if isinstance(op_param, TapOp):
            self.ui_area = op_param.area
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            res = env.step(EnvAPIAbstract(api_name="system_tap", kwargs={"x": x, "y": y}))
            if res == ADB_EXEC_FAIL:
                return AndroidActionOutput(action_state=RunState.FAIL)
        elif isinstance(op_param, TextOp):
            res = env.step(EnvAPIAbstract(api_name="user_input", kwargs={"input_txt": op_param.input_str}))
            if res == ADB_EXEC_FAIL:
                return AndroidActionOutput(action_state=RunState.FAIL)
        elif isinstance(op_param, LongPressOp):
            self.ui_area = op_param.area
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            res = env.step(EnvAPIAbstract(api_name="user_longpress", kwargs={"x": x, "y": y}))
            if res == ADB_EXEC_FAIL:
                return AndroidActionOutput(action_state=RunState.FAIL)
        elif isinstance(op_param, SwipeOp):
            self.ui_area = op_param.area
            self.swipe_orient = op_param.swipe_orient
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            res = env.step(
                EnvAPIAbstract(
                    "user_swipe", kwargs={"x": x, "y": y, "orient": op_param.swipe_orient, "dist": op_param.dist}
                )
            )
            if res == ADB_EXEC_FAIL:
                return AndroidActionOutput(action_state=RunState.FAIL)

        self.elem_list = elem_list
        self.act_name = op_param.act_name
        return AndroidActionOutput()

    async def run_reflect(
            self, round_count: int, task_desc: str, last_act: str, task_dir: Path, docs_dir: Path, env: AndroidEnv
    ) -> AndroidActionOutput:
        logger.info("run_reflect")
        screenshot_path: Path = env.observe(
            EnvAPIAbstract(
                api_name="get_screenshot", kwargs={"ss_name": f"{round_count}_after", "local_save_dir": task_dir}
            )
        )
        if not screenshot_path.exists():
            return AndroidActionOutput(action_state=RunState.FAIL)

        screenshot_after_labeled_path = task_dir.joinpath(f"{round_count}_after_labeled.png")
        draw_bbox_multi(screenshot_path, screenshot_after_labeled_path, elem_list=self.elem_list)
        img_base64 = encode_image(screenshot_after_labeled_path)

        logger.info(f"act_name: {self.act_name}")
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
        context = reflect_template.format(
            action=action, ui_element=str(self.ui_area), task_desc=task_desc, last_act=last_act
        )
        node = await SELF_LEARN_REFLECT_NODE.fill(
            context=context, llm=self.llm, images=[self.screenshot_before_base64, img_base64]
        )

        if "error" in node.content:
            return AndroidActionOutput(action_state=RunState.FAIL)

        prompt = node.compile(context=context, schema="json", mode="auto")
        ReflectLogItem(
            step=round_count,
            prompt=prompt,
            image_before=str(self.screenshot_before_path),
            image_after=str(screenshot_after_labeled_path),
            response=node.content,
        )

        op_param = reflect_parse_extarct(node.instruct_content.model_dump())
        if op_param.param_state == RunState.FINISH:
            return AndroidActionOutput(action_state=RunState.FINISH)
        if op_param.param_state == RunState.FAIL:
            return AndroidActionOutput(action_state=RunState.FAIL)

        resource_id = self.elem_list[int(self.ui_area) - 1].uid
        if op_param.decision == Decision.INEFFECTIVE.value:
            self.useless_list.append(resource_id)
            last_act = "NONE"  # TODO global
        elif op_param.decision in [Decision.BACK.value, Decision.CONTINUE.value, Decision.SUCCESS.value]:
            if op_param.decision in [Decision.BACK.value, Decision.CONTINUE.value]:
                self.useless_list.append(resource_id)
                last_act = "NONE"
                if op_param.decision == Decision.BACK.value:
                    res = env.step(EnvAPIAbstract(api_name="system_back"))
                    if res == ADB_EXEC_FAIL:
                        return AndroidActionOutput(action_state=RunState.FAIL)
            doc = op_param.documentation
            doc_path = docs_dir.joinpath(f"{resource_id}.txt")
            if doc_path.exists():
                doc_content = ast.literal_eval(open(doc_path).read())
                if doc_content[self.act_name]:
                    logger.info(f"Documentation for the element {resource_id} already exists.")
                    return AndroidActionOutput(action_state=RunState.FAIL)
            else:
                doc_content = DocContent()
                setattr(doc_content, self.act_name, doc)
            doc_path.write_text(str(doc_content))

        return AndroidActionOutput(data={"last_act": last_act})
