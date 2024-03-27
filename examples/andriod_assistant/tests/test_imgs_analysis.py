#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : test case (imgs from appagent's)

import ast
import asyncio
import re

from examples.andriod_assistant.actions.parse_record_an import RECORD_PARSE_NODE
from examples.andriod_assistant.prompts.operation_prompt import (
    long_press_doc_template,
    refine_doc_suffix,
    swipe_doc_template,
    tap_doc_template,
    text_doc_template,
)
from examples.andriod_assistant.utils.const import ROOT_PATH
from examples.andriod_assistant.utils.schema import ActionOp, SwipeOp
from metagpt.actions.action import Action
from metagpt.config2 import config
from metagpt.logs import logger
from metagpt.utils.common import encode_image

TASK_PATH = ROOT_PATH.parent.joinpath("data/demo_Contacts")
TEST_BEFORE_PATH = TASK_PATH.joinpath("labeled_screenshots/demo_Contacts_2024-01-24_12-07-55_3.png")
TEST_AFTER_PATH = TASK_PATH.joinpath("labeled_screenshots/demo_Contacts_2024-01-24_12-07-55_4.png")
RECORD_PATH = TASK_PATH.joinpath("record.txt")
TASK_DESC_PATH = TASK_PATH.joinpath("task_desc.txt")
DOCS_DIR = TASK_PATH.joinpath("storage")

test_action = Action(name="test")


async def manual_test():
    img_before_base64 = encode_image(TEST_BEFORE_PATH)
    img_after_base64 = encode_image(TEST_AFTER_PATH)

    with open(RECORD_PATH, "r") as record_file:
        rec = record_file.readline().strip()
        action, resource_id = rec.split(":::")
        action_type = action.split("(")[0]
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
            logger.error("Error occurs")

        task_desc_path = TASK_DESC_PATH
        task_desc = open(task_desc_path, "r").read()
        context = context.format(task_desc=task_desc)

        doc_name = resource_id + ".txt"

        doc_path = DOCS_DIR.joinpath(doc_name)
        if doc_path.exists():
            doc_content = ast.literal_eval(open(doc_path).read())
            if doc_content[action_type]:
                if config.get_other("doc_refine"):
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
        else:
            doc_content = {"tap": "", "text": "", "v_swipe": "", "h_swipe": "", "long_press": ""}
        logger.info(f"Waiting for GPT-4V to generate documentation for the element {resource_id}")

        node = await RECORD_PARSE_NODE.fill(
            context=context, llm=test_action.llm, images=[img_before_base64, img_after_base64]
        )

        node.compile(context=context, schema="json", mode="auto")
        msg = node.content
        doc_content[action_type] = msg

        with open(doc_path, "w") as outfile:
            outfile.write(str(doc_content))
        logger.info(f"Documentation generated and saved to {doc_path}")


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(manual_test())
    loop.close()
