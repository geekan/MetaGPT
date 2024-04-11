#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : parse record to generate learned standard operations in stage=learn & mode=manual,
#           LIKE scripts/document_generation.py

import ast
import re
from pathlib import Path

from metagpt.actions.action import Action
from metagpt.config2 import config
from metagpt.ext.android_assistant.actions.parse_record_an import RECORD_PARSE_NODE
from metagpt.ext.android_assistant.prompts.operation_prompt import (
    long_press_doc_template,
    refine_doc_suffix,
    swipe_doc_template,
    tap_doc_template,
    text_doc_template,
)
from metagpt.ext.android_assistant.utils.schema import (
    ActionOp,
    AndroidActionOutput,
    RecordLogItem,
    RunState,
    SwipeOp,
)
from metagpt.logs import logger
from metagpt.utils.common import encode_image


class ParseRecord(Action):
    name: str = "ParseRecord"
    record_path: Path = ""
    task_desc_path: Path = ""
    screenshot_before_path: Path = ""
    screenshot_after_path: Path = ""

    async def run(self, task_dir: Path, docs_dir: Path):
        doc_count = 0
        self.record_path = Path(task_dir) / "record.txt"
        self.task_desc_path = Path(task_dir) / "task_desc.txt"
        self.screenshot_before_path = Path(task_dir) / "raw_screenshots"
        self.screenshot_after_path = Path(task_dir) / "labeled_screenshots"
        for path in [self.screenshot_before_path, self.screenshot_after_path]:
            path.mkdir(parents=True, exist_ok=True)

        task_desc = self.task_desc_path.read_text()
        extra_config = config.extra

        with open(self.record_path, "r") as record_file:
            record_step_count = len(record_file.readlines()) - 1
            record_file.seek(0)
            for step in range(1, record_step_count + 1):
                img_before_base64 = encode_image(self.screenshot_after_path.joinpath(f"{step}_labeled.png"))
                img_after_base64 = encode_image(self.screenshot_after_path.joinpath(f"{step + 1}_labeled.png"))
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
                context = context.format(task_desc=task_desc)

                doc_name = resource_id + ".txt"
                doc_path = docs_dir.joinpath(doc_name)

                if doc_path.exists():
                    try:
                        doc_content = ast.literal_eval(doc_path.read_text())
                    except Exception as exp:
                        logger.error(f"ast parse doc: {doc_path} failed, exp: {exp}")
                        continue

                    if doc_content[action_type]:
                        if extra_config.get("doc_refine", False):
                            refine_context = refine_doc_suffix.format(old_doc=doc_content[action_type])
                            context += refine_context
                            logger.info(
                                f"Documentation for the element {resource_id} already exists. The doc will be "
                                f"refined based on the latest demo."
                            )
                        else:
                            logger.info(
                                f"Documentation for the element {resource_id} already exists. Turn on DOC_REFINE "
                                f"in the config file if needed."
                            )
                            continue
                else:
                    doc_content = {"tap": "", "text": "", "v_swipe": "", "h_swipe": "", "long_press": ""}

                logger.info(f"Waiting for GPT-4V to generate documentation for the element {resource_id}")
                node = await RECORD_PARSE_NODE.fill(
                    context=context, llm=self.llm, images=[img_before_base64, img_after_base64]
                )
                if "error" in node.content:
                    return AndroidActionOutput(action_state=RunState.FAIL)
                log_path = task_dir.joinpath("log_parse_record.txt")
                prompt = node.compile(context=context, schema="json", mode="auto")
                msg = node.content
                doc_content[action_type] = msg

                with open(log_path, "a") as logfile:
                    log_item = RecordLogItem(
                        step=step,
                        prompt=prompt,
                        image_before=img_before_base64,
                        image_after=img_after_base64,
                        response=node.content,
                    )
                    logfile.write(log_item.model_dump_json() + "\n")
                with open(doc_path, "w") as outfile:
                    outfile.write(str(doc_content))
                doc_count += 1
                logger.info(f"Documentation generated and saved to {doc_path}")

            logger.info(f"Documentation generation phase completed. {doc_count} docs generated.")

        return AndroidActionOutput(action_state=RunState.FINISH)
