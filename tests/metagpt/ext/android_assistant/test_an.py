#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : test on android emulator action. After Modify Role Test, this script is discarded.

import asyncio
import time
from pathlib import Path

import metagpt
from metagpt.const import TEST_DATA_PATH
from metagpt.environment.android.android_env import AndroidEnv
from metagpt.ext.android_assistant.actions.manual_record import ManualRecord
from metagpt.ext.android_assistant.actions.parse_record import ParseRecord
from metagpt.ext.android_assistant.actions.screenshot_parse import ScreenshotParse
from metagpt.ext.android_assistant.actions.self_learn_and_reflect import (
    SelfLearnAndReflect,
)
from tests.metagpt.environment.android_env.test_android_ext_env import (
    mock_device_shape,
    mock_list_devices,
)

TASK_PATH = TEST_DATA_PATH.joinpath("andriod_assistant/unitest_Contacts")
TASK_PATH.mkdir(parents=True, exist_ok=True)
DEMO_NAME = str(time.time())
SELF_EXPLORE_DOC_PATH = TASK_PATH.joinpath("auto_docs")
PARSE_RECORD_DOC_PATH = TASK_PATH.joinpath("demo_docs")

device_id = "emulator-5554"
xml_dir = Path("/sdcard")
screenshot_dir = Path("/sdcard/Pictures/Screenshots")


metagpt.environment.android.android_ext_env.AndroidExtEnv.execute_adb_with_cmd = mock_device_shape
metagpt.environment.android.android_ext_env.AndroidExtEnv.list_devices = mock_list_devices


test_env_self_learn_android = AndroidEnv(
    device_id=device_id,
    xml_dir=xml_dir,
    screenshot_dir=screenshot_dir,
)
test_self_learning = SelfLearnAndReflect()

test_env_manual_learn_android = AndroidEnv(
    device_id=device_id,
    xml_dir=xml_dir,
    screenshot_dir=screenshot_dir,
)
test_manual_record = ManualRecord()
test_manual_parse = ParseRecord()

test_env_screenshot_parse_android = AndroidEnv(
    device_id=device_id,
    xml_dir=xml_dir,
    screenshot_dir=screenshot_dir,
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
            task_dir=TASK_PATH / "demos" / f"manual_record_{DEMO_NAME}",
            task_desc="Create a contact in Contacts App named zjy with a phone number +86 18831933368 ",
            env=test_env_manual_learn_android,
        ),
        test_manual_parse.run(
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
