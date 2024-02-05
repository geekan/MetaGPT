#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : test on android emulator
import asyncio
import time
from pathlib import Path
from actions.manual_record import ManualRecord
from actions.parse_record import ParseRecord
from actions.self_learn_and_reflect import SelfLearnAndReflect
from metagpt.environment.android_env.android_env import AndroidEnv

TASK_PATH = Path("apps/Contacts")
DOC_PATH = TASK_PATH.joinpath("docs")
DEMO_NAME = str(time.time())
# TODO Test for Self Learning、
test_env_self_learn_android = AndroidEnv(
    device_id="emulator-5554",
    xml_dir=Path("/sdcard"),
    screenshot_dir=Path("/sdcard/Pictures/Screenshots"),
)
test_self_learning = SelfLearnAndReflect()

# TODO Test for Manual Learning
test_env_manual_learn_android = AndroidEnv(
    device_id="emulator-5554",
    xml_dir=Path("/sdcard"),
    screenshot_dir=Path("/sdcard/Pictures/Screenshots"),
)
test_manual_record = ManualRecord()
test_manual_parse = ParseRecord()

# 虚拟机效果实现
# 不同 Action Node 结果符合预期(Action Node)

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    test_action_list = [
        test_self_learning.run(
            round_count=20,
            task_desc="Create a contact in Contacts App named zjy with a phone number +86 18831933368 ",
            last_act="",
            task_dir=TASK_PATH,
            docs_dir=DOC_PATH,
            env=test_env_self_learn_android
        ),
        # test_manual_record.run(
        #     demo_name=DEMO_NAME,
        #     task_dir=TASK_PATH,
        #     env=test_env_manual_learn_android
        # ),
        # test_manual_parse.run(
        #     app_name="Contacts",
        #     demo_name=DEMO_NAME,
        #     task_dir=TASK_PATH,
        #     docs_dir=DOC_PATH,
        #     env=test_env_manual_learn_android
        # )
    ]
    loop.run_until_complete(asyncio.gather(*test_action_list))
    loop.close()
    print("Finish")
