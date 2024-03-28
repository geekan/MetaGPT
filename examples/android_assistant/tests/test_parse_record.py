#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : test case (imgs from appagent's)

import asyncio

from examples.android_assistant.actions.parse_record import ParseRecord
from examples.android_assistant.utils.const import ROOT_PATH
from metagpt.actions.action import Action

TASK_PATH = ROOT_PATH.parent.joinpath("data/demo_Contacts")
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
