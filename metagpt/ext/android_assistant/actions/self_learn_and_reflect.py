# !/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : LIKE scripts/self_explorer.py in stage=learn & mode=auto self_explore_task stage

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
from metagpt.ext.android_assistant.actions.self_learn_reflect_an import (
    SELF_LEARN_REFLECT_NODE,
)
from metagpt.ext.android_assistant.prompts.assistant_prompt import (
    screenshot_parse_self_explore_reflect_template as reflect_template,
)
from metagpt.ext.android_assistant.prompts.assistant_prompt import (
    screenshot_parse_self_explore_template,
)
from metagpt.ext.android_assistant.utils.schema import (
    ActionOp,
    AndroidActionOutput,
    AndroidElement,
    Decision,
    DocContent,
    LongPressOpParam,
    OpLogItem,
    ReflectLogItem,
    RunState,
    SwipeOp,
    SwipeOpParam,
    TapOpParam,
    TextOpParam,
)
from metagpt.ext.android_assistant.utils.utils import (
    draw_bbox_multi,
    elem_bbox_to_xy,
    elem_list_from_xml_tree,
    reflect_parse_extarct,
    screenshot_parse_extract,
)
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
        for path in [task_dir, docs_dir]:
            path.mkdir(parents=True, exist_ok=True)
        resp = await self.run_self_learn(round_count, task_desc, last_act, task_dir, env)
        if resp.action_state != RunState.SUCCESS:
            return resp

        resp = await self.run_reflect(round_count, task_desc, last_act, task_dir, docs_dir, env)
        return resp

    async def run_self_learn(
        self, round_count: int, task_desc: str, last_act: str, task_dir: Path, env: AndroidEnv
    ) -> AndroidActionOutput:
        extra_config = config.extra
        screenshot_path: Path = env.observe(
            EnvObsParams(obs_type=EnvObsType.GET_SCREENSHOT, ss_name=f"{round_count}_before", local_save_dir=task_dir)
        )
        xml_path: Path = env.observe(
            EnvObsParams(obs_type=EnvObsType.GET_XML, xml_name=f"{round_count}", local_save_dir=task_dir)
        )
        if not screenshot_path.exists() or not xml_path.exists():
            return AndroidActionOutput(action_state=RunState.FAIL)

        elem_list = elem_list_from_xml_tree(xml_path, self.useless_list, extra_config.get("min_dist", 30))

        screenshot_before_labeled_path = task_dir.joinpath(f"{round_count}_before_labeled.png")
        draw_bbox_multi(screenshot_path, screenshot_before_labeled_path, elem_list)
        img_base64 = encode_image(screenshot_before_labeled_path)
        self.screenshot_before_base64 = img_base64
        self.screenshot_before_path = screenshot_before_labeled_path

        self_explore_template = screenshot_parse_self_explore_template
        context = self_explore_template.format(task_description=task_desc, last_act=last_act)

        node = await SCREENSHOT_PARSE_NODE.fill(context=context, llm=self.llm, images=[img_base64])
        logger.debug(f"fill result:{node}")
        if "error" in node.content:
            return AndroidActionOutput(action_state=RunState.FAIL)
        prompt = node.compile(context=context, schema="json", mode="auto")
        # Modify WindowsPath to Str
        OpLogItem(step=round_count, prompt=prompt, image=str(screenshot_before_labeled_path), response=node.content)
        op_param = screenshot_parse_extract(node.instruct_content.model_dump(), grid_on=False)
        # TODO Modify Op_param. When op_param.action is FINISH, how to solve this ?
        if op_param.param_state == RunState.FINISH:
            return AndroidActionOutput(action_state=RunState.FINISH)
        if op_param.param_state == RunState.FAIL:
            return AndroidActionOutput(action_state=RunState.FAIL)

        if isinstance(op_param, TapOpParam):
            self.ui_area = op_param.area
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            action = EnvAction(action_type=EnvActionType.SYSTEM_TAP, coord=(x, y))
        elif isinstance(op_param, TextOpParam):
            action = EnvAction(action_type=EnvActionType.USER_INPUT, input_txt=op_param.input_str)
        elif isinstance(op_param, LongPressOpParam):
            self.ui_area = op_param.area
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            action = EnvAction(action_type=EnvActionType.USER_LONGPRESS, coord=(x, y))
        elif isinstance(op_param, SwipeOpParam):
            self.ui_area = op_param.area
            self.swipe_orient = op_param.swipe_orient
            x, y = elem_bbox_to_xy(elem_list[op_param.area - 1].bbox)
            action = EnvAction(
                action_type=EnvActionType.USER_SWIPE, coord=(x, y), orient=op_param.swipe_orient, dist=op_param.dist
            )

        obs, _, _, _, info = env.step(action)
        action_res = info["res"]
        if action_res == ADB_EXEC_FAIL:
            return AndroidActionOutput(action_state=RunState.FAIL)

        self.elem_list = elem_list
        self.act_name = op_param.act_name
        return AndroidActionOutput()

    async def run_reflect(
        self, round_count: int, task_desc: str, last_act: str, task_dir: Path, docs_dir: Path, env: AndroidEnv
    ) -> AndroidActionOutput:
        screenshot_path: Path = env.observe(
            EnvObsParams(obs_type=EnvObsType.GET_SCREENSHOT, ss_name=f"{round_count}_after", local_save_dir=task_dir)
        )
        if not screenshot_path.exists():
            return AndroidActionOutput(action_state=RunState.FAIL)

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
        else:
            # TODO Test for assignment, This error is eupiped with the next.
            logger.warning(f"Current action name parse failed, it's `{self.act_name}`")
            action = None
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

        logger.info(
            f"reflect_parse_extarct decision: {op_param.decision}, "
            f"elem_list size: {len(self.elem_list)}, ui_area: {self.ui_area}"
        )
        # TODO here will cause `IndexError: list index out of range`.
        #  Maybe you should clink back to the desktop in the simulator
        resource_id = self.elem_list[int(self.ui_area) - 1].uid
        if op_param.decision == Decision.INEFFECTIVE.value:
            self.useless_list.append(resource_id)
            last_act = "NONE"  # TODO global
        elif op_param.decision in [Decision.BACK.value, Decision.CONTINUE.value, Decision.SUCCESS.value]:
            if op_param.decision in [Decision.BACK.value, Decision.CONTINUE.value]:
                self.useless_list.append(resource_id)
                last_act = "NONE"
                if op_param.decision == Decision.BACK.value:
                    action = EnvAction(action_type=EnvActionType.SYSTEM_BACK)
                    obs, _, _, _, info = env.step(action)
                    if info["res"] == ADB_EXEC_FAIL:
                        return AndroidActionOutput(action_state=RunState.FAIL)
            doc = op_param.documentation
            doc_path = docs_dir.joinpath(f"{resource_id}.txt")
            if doc_path.exists():
                try:
                    doc_content = ast.literal_eval(doc_path.read_text())
                except Exception as exp:
                    logger.error(f"ast parse doc: {doc_path} failed, exp: {exp}")
                    return AndroidActionOutput(action_state=RunState.FAIL)

                if doc_content[self.act_name]:
                    logger.info(f"Documentation for the element {resource_id} already exists.")
                    return AndroidActionOutput(action_state=RunState.FAIL)
            else:
                doc_content = DocContent()
                setattr(doc_content, self.act_name, doc)
            doc_path.write_text(str(doc_content))
        return AndroidActionOutput(data={"last_act": last_act})
