#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : test case (imgs from appagent's)

import asyncio

from metagpt.actions.action import Action
from metagpt.const import TEST_DATA_PATH
from metagpt.ext.android_assistant.actions.parse_record import ParseRecord

TASK_PATH = TEST_DATA_PATH.joinpath("andriod_assistant/demo_Contacts")
TEST_BEFORE_PATH = TASK_PATH.joinpath("labeled_screenshots/0_labeled.png")
TEST_AFTER_PATH = TASK_PATH.joinpath("labeled_screenshots/1_labeled.png")
RECORD_PATH = TASK_PATH.joinpath("record.txt")
TASK_DESC_PATH = TASK_PATH.joinpath("task_desc.txt")
DOCS_DIR = TASK_PATH.joinpath("storage")

test_action = Action(name="test")


async def manual_learn_test():
    parse_record = ParseRecord()
    await parse_record.run(app_name="demo_Contacts", task_dir=TASK_PATH, docs_dir=DOCS_DIR)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(manual_learn_test())
    loop.close()
