#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Desc   : the entry of android assistant including learning and acting stage

import asyncio
from pathlib import Path

import typer

from examples.andriod_assistant.roles.android_assistant import AndroidAssistant
from metagpt.config2 import config
from metagpt.environment.android_env.android_env import AndroidEnv
from metagpt.team import Team

app = typer.Typer(add_completion=False, pretty_exceptions_show_locals=False)


@app.command("", help="Run a Android Assistant")
def startup(
    task_desc: str = typer.Argument(help="the task description you want the android assistant to learn or act"),
    n_round: int = typer.Option(default=20, help="The max round to do an app operation task."),
    stage: str = typer.Option(default="learn", help="stage: learn / act"),
    mode: str = typer.Option(default="auto", help="mode: auto / manual , when state=learn"),
    app_name: str = typer.Option(default="demo", help="the name of app you want to run"),
    investment: float = typer.Option(default=5.0, help="Dollar amount to invest in the AI company."),
    refine_doc: bool = typer.Option(
        default=False, help="Refine existing operation docs based on the latest observation if True."
    ),
    min_dist: int = typer.Option(
        default=30, help="The minimum distance between elements to prevent overlapping during the labeling process."
    ),
    android_screenshot_dir: str = typer.Option(
        default="/sdcard/Pictures/Screenshots",
        help="The path to store screenshots on android device. Make sure it exists.",
    ),
    android_xml_dir: str = typer.Option(
        default="/sdcard",
        help="The path to store xml files for determining UI elements localtion. Make sure it exists.",
    ),
    device_id: str = typer.Option(default="emulator-5554", help="The Android device_id"),
):
    config.set_other(
        {
            "stage": stage,
            "mode": mode,
            "app_name": app_name,
            "refine_doc": refine_doc,
            "min_dist": min_dist,
            "android_screenshot_dir": android_screenshot_dir,
            "android_xml_dir": android_xml_dir,
            "device_id": device_id,
        }
    )

    team = Team(
        env=AndroidEnv(
            device_id=device_id,
            xml_dir=Path(android_xml_dir),
            screenshot_dir=Path(android_screenshot_dir),
        )
    )

    team.hire([AndroidAssistant()])
    team.invest(investment)
    team.run_project(idea=task_desc)
    asyncio.run(team.run(n_round=n_round))


if __name__ == "__main__":
    app()
# Command python run_assistant.py "Create a contact in Contacts App named zjy with a phone number +86 18831933368"

# python run_assistant.py "Create a contact in Contacts App named zjy with a phone number +86 18831933368" --mode "auto" --app-name "Contacts"examples\andriod_assistant>

# TODO
# 0. How to set Round ?
# 1. Manual Record & Parse Record Success
# 2. Self Learn Fail
#   local variable 'action' referenced before assignment
# 3. Act
#   3.1 TODO Act with Manual Docs
#   3.2 TDOO Act with Auto Docs
