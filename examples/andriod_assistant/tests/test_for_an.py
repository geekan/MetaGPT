#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : test on android emulator action. After Modify Role Test, this script is discarded.

import asyncio
import time
from pathlib import Path

from examples.andriod_assistant.actions.manual_record import ManualRecord
from examples.andriod_assistant.actions.parse_record import ParseRecord
from examples.andriod_assistant.actions.screenshot_parse import ScreenshotParse
from examples.andriod_assistant.actions.self_learn_and_reflect import (
    SelfLearnAndReflect,
)
from metagpt.environment.android_env.android_env import AndroidEnv

TASK_PATH = Path("apps/Contacts")
DEMO_NAME = str(time.time())
SELF_EXPLORE_DOC_PATH = TASK_PATH.joinpath("autodocs")
PARSE_RECORD_DOC_PATH = TASK_PATH.joinpath("demodocs")

test_env_self_learn_android = AndroidEnv(
    device_id="emulator-5554",
    xml_dir=Path("/sdcard"),
    screenshot_dir=Path("/sdcard/Pictures/Screenshots"),
)
test_self_learning = SelfLearnAndReflect()

test_env_manual_learn_android = AndroidEnv(
    device_id="emulator-5554",
    xml_dir=Path("/sdcard"),
    screenshot_dir=Path("/sdcard/Pictures/Screenshots"),
)
test_manual_record = ManualRecord()
test_manual_parse = ParseRecord()

test_env_screenshot_parse_android = AndroidEnv(
    device_id="emulator-5554",
    xml_dir=Path("/sdcard"),
    screenshot_dir=Path("/sdcard/Pictures/Screenshots"),
)
test_screenshot_parse = ScreenshotParse()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    test_action_list = [
        test_self_learning.run(
            round_count=20,
            task_desc="Create a contact in Contacts App named zjy with a phone number +86 18831933368 ",
            last_act="",
            task_dir=TASK_PATH / "demos" / f"self_learning_{DEMO_NAME}",
            docs_dir=SELF_EXPLORE_DOC_PATH,
            env=test_env_self_learn_android,
        ),
        test_manual_record.run(
            # demo_name=DEMO_NAME,
            task_dir=TASK_PATH / "demos" / f"manual_record_{DEMO_NAME}",
            task_desc="Create a contact in Contacts App named zjy with a phone number +86 18831933368 ",
            env=test_env_manual_learn_android,
        ),
        test_manual_parse.run(
            app_name="Contacts",
            # demo_name=DEMO_NAME,
            task_dir=TASK_PATH / "demos" / f"manual_record_{DEMO_NAME}",  # 修要修改
            docs_dir=PARSE_RECORD_DOC_PATH,  # 需要修改
            env=test_env_manual_learn_android,
        ),
        test_screenshot_parse.run(
            round_count=20,
            task_desc="Create a contact in Contacts App named zjy with a phone number +86 18831933368 ",
            last_act="",
            task_dir=TASK_PATH / f"act_{DEMO_NAME}",
            docs_dir=PARSE_RECORD_DOC_PATH,
            env=test_env_screenshot_parse_android,
            grid_on=False,
        ),
    ]

    loop.run_until_complete(asyncio.gather(*test_action_list))
    loop.close()
