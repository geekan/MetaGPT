#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/27
@Author  : mashenquan
@File    : teacher.py
@Desc    : Used by Agent Store
@Modified By: mashenquan, 2023/8/22. A definition has been provided for the return value of _think: returning false indicates that further reasoning cannot continue.

"""

import re

from metagpt.actions import UserRequirement
from metagpt.actions.write_teaching_plan import TeachingPlanBlock, WriteTeachingPlanPart
from metagpt.logs import logger
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.utils.common import any_to_str, awrite


class Teacher(Role):
    """Support configurable teacher roles,
    with native and teaching languages being replaceable through configurations."""

    name: str = "Lily"
    profile: str = "{teaching_language} Teacher"
    goal: str = "writing a {language} teaching plan part by part"
    constraints: str = "writing in {language}"
    desc: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = WriteTeachingPlanPart.format_value(self.name, self.context)
        self.profile = WriteTeachingPlanPart.format_value(self.profile, self.context)
        self.goal = WriteTeachingPlanPart.format_value(self.goal, self.context)
        self.constraints = WriteTeachingPlanPart.format_value(self.constraints, self.context)
        self.desc = WriteTeachingPlanPart.format_value(self.desc, self.context)

    async def _think(self) -> bool:
        """Everything will be done part by part."""
        if not self.actions:
            if not self.rc.news or self.rc.news[0].cause_by != any_to_str(UserRequirement):
                raise ValueError("Lesson content invalid.")
            actions = []
            print(TeachingPlanBlock.TOPICS)
            for topic in TeachingPlanBlock.TOPICS:
                act = WriteTeachingPlanPart(i_context=self.rc.news[0].content, topic=topic, llm=self.llm)
                actions.append(act)
            self.set_actions(actions)

        if self.rc.todo is None:
            self._set_state(0)
            return True

        if self.rc.state + 1 < len(self.states):
            self._set_state(self.rc.state + 1)
            return True

        self.set_todo(None)
        return False

    async def _react(self) -> Message:
        ret = Message(content="")
        while True:
            await self._think()
            if self.rc.todo is None:
                break
            logger.debug(f"{self._setting}: {self.rc.state=}, will do {self.rc.todo}")
            msg = await self._act()
            if ret.content != "":
                ret.content += "\n\n\n"
            ret.content += msg.content
        logger.info(ret.content)
        await self.save(ret.content)
        return ret

    async def save(self, content):
        """Save teaching plan"""
        filename = Teacher.new_file_name(self.course_title)
        pathname = self.config.workspace.path / "teaching_plan"
        pathname.mkdir(exist_ok=True)
        pathname = pathname / filename
        await awrite(pathname, content)
        logger.info(f"Save to:{pathname}")

    @staticmethod
    def new_file_name(lesson_title, ext=".md"):
        """Create a related file name based on `lesson_title` and `ext`."""
        # Define the special characters that need to be replaced.
        illegal_chars = r'[#@$%!*&\\/:*?"<>|\n\t \']'
        # Replace the special characters with underscores.
        filename = re.sub(illegal_chars, "_", lesson_title) + ext
        return re.sub(r"_+", "_", filename)

    @property
    def course_title(self):
        """Return course title of teaching plan"""
        default_title = "teaching_plan"
        for act in self.actions:
            if act.topic != TeachingPlanBlock.COURSE_TITLE:
                continue
            if act.rsp is None:
                return default_title
            title = act.rsp.lstrip("# \n")
            if "\n" in title:
                ix = title.index("\n")
                title = title[0:ix]
            return title

        return default_title
