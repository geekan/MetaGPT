#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : parse record to generate learned standard operations in stage=learn & mode=manual,
#           LIKE scripts/document_generation.py

import re
import ast
import json
import time
from pathlib import Path

from examples.andriod_assistant.prompts.operation_prompt import (
    tap_doc_template,
    text_doc_template,
    long_press_doc_template,
    swipe_doc_template,
    refine_doc_suffix
)
from examples.andriod_assistant.utils.schema import RecordLogItem, RunState, ActionOp, \
    SwipeOp, AndroidActionOutput
from examples.andriod_assistant.actions.parse_record_an import RECORD_PARSE_NODE
from metagpt.config2 import config
from metagpt.environment.android_env.android_env import AndroidEnv
from metagpt.utils.common import encode_image
from metagpt.logs import logger
from metagpt.actions.action import Action


class ParseRecord(Action):
    name: str = "ParseRecord"

    async def run(
            self, app_name: str, demo_name: str, task_dir: Path, docs_dir: Path, env: AndroidEnv
    ):
        doc_count = 0
        record_path = Path(task_dir) / "record.txt"

        with open(record_path, "r") as record_file:
            record_step_count = len(record_file.readlines()) - 1
            record_file.seek(0)
            for step in range(1, record_step_count + 1):
                img_before_base64 = encode_image(task_dir.joinpath(f"{task_dir}_{step}_labeled.png"))
                img_after_base64 = encode_image(task_dir.joinpath(f"{task_dir}_{step + 1}_labeled.png"))
                rec = record_file.readline().strip()
                action, resource_id = rec.split(":::")
                action_type = action.split("(")[0]
                # 构建Prompt
                action_param = re.findall(r"\((.*?)\)", action)[0]
                if action_type == ActionOp.TAP.value:
                    prompt_template = tap_doc_template
                    context = prompt_template.format(ui_element=action_param)
                elif action_type == ActionOp.TEXT.value:
                    input_area, input_text = action_param.split(":sep:")
                    prompt_template = text_doc_template
                    context = prompt_template.format(ui_element=input_area)
                elif action_type == ActionOp.LONG_PRESS.value:
                    prompt_template = long_press_doc_template
                    context = prompt_template.format(ui_element=action_param)
                elif action_type == ActionOp.SWIPE.value:
                    swipe_area, swipe_dir = action_param.split(":sep:")
                    if swipe_dir == SwipeOp.UP.value or swipe_dir == SwipeOp.DOWN.value:
                        action_type = ActionOp.VERTICAL_SWIPE.value
                    elif swipe_dir == SwipeOp.LEFT.value or swipe_dir == SwipeOp.RIGHT.value:
                        action_type = ActionOp.HORIZONTAL_SWIPE.value
                    prompt_template = swipe_doc_template
                    context = prompt_template.format(swipe_dir=swipe_dir, ui_element=swipe_area)
                else:
                    break
                task_desc_path = task_dir.joinpath("task_desc.txt")
                task_desc = open(task_desc_path, "r").read()
                context = context.format(task_desc=task_desc)

                doc_name = resource_id + ".txt"
                doc_path = docs_dir.joinpath(doc_name)

                if doc_path.exists():
                    doc_content = ast.literal_eval(open(doc_path).read())
                    if doc_content[action_type]:
                        if config.get_other("doc_refine"):
                            refine_context = refine_doc_suffix.format(old_doc=doc_content[action_type])
                            context += refine_context
                            logger.info(
                                f"Documentation for the element {resource_id} already exists. The doc will be "
                                f"refined based on the latest demo.")
                        else:
                            logger.info(
                                f"Documentation for the element {resource_id} already exists. Turn on DOC_REFINE "
                                f"in the config file if needed.")
                            continue
                else:
                    doc_content = {
                        "tap": "",
                        "text": "",
                        "v_swipe": "",
                        "h_swipe": "",
                        "long_press": ""
                    }

                logger.info(f"Waiting for GPT-4V to generate documentation for the element {resource_id}")
                node = await RECORD_PARSE_NODE.fill(context=context, llm=self.llm,
                                                    images=[img_before_base64, img_after_base64])
                if "error" in node.content:
                    return AndroidActionOutput(action_state=RunState.FAIL)

                log_path = task_dir.joinpath(f"log_{app_name}_{demo_name}.txt")
                prompt = node.compile(context=context, schema="json", mode="auto")
                msg = node.content
                doc_content[action_type] = msg

                with open(log_path, "a") as logfile:
                    log_item = RecordLogItem(step=step, prompt=prompt, image_before=img_before_base64,
                                             image_after=img_after_base64, response=node.content)
                    # TODO 修改 dumps 方式
                    logfile.write(json.dumps(log_item) + "\n")
                with open(doc_path, "w") as outfile:
                    outfile.write(str(doc_content))
                doc_count += 1
                logger.info(f"Documentation generated and saved to {doc_path}")

                time.sleep(config.get_other("request_interval"))

            logger.info(f"Documentation generation phase completed. {doc_count} docs generated.")
