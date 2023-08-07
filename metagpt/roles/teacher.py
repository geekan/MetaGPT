#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Time    : 2023/7/27
@Author  : mashenquan
@File    : teacher.py
"""


import aiofiles

from metagpt.actions.write_teaching_plan import WriteTeachingPlanPart, TeachingPlanRequirement
from metagpt.const import WORKSPACE_ROOT
from metagpt.roles import Role
from metagpt.schema import Message
from metagpt.logs import logger
import re


class Teacher(Role):
    """Support configurable teacher roles,
    with native and teaching languages being replaceable through configurations."""
    def __init__(self, name='Lily', profile='{teaching_language} Teacher',
                 goal='writing a {language} teaching plan part by part',
                 constraints='writing in {language}', desc="", *args, **kwargs):
        super().__init__(name=name, profile=profile, goal=goal, constraints=constraints, desc=desc, *args, **kwargs)
        actions = []
        for topic in WriteTeachingPlanPart.TOPICS:
            act = WriteTeachingPlanPart(topic=topic, llm=self._llm)
            actions.append(act)
        self._init_actions(actions)
        self._watch({TeachingPlanRequirement})

    async def _think(self) -> None:
        """Everything will be done part by part."""
        if self._rc.todo is None:
            self._set_state(0)
            return

        if self._rc.state + 1 < len(self._states):
            self._set_state(self._rc.state + 1)
        else:
            self._rc.todo = None

    async def _react(self) -> Message:
        ret = Message(content="")
        while True:
            await self._think()
            if self._rc.todo is None:
                break
            logger.debug(f"{self._setting}: {self._rc.state=}, will do {self._rc.todo}")
            msg = await self._act()
            if ret.content != '':
                ret.content += "\n\n\n"
            ret.content += msg.content
        logger.info(ret.content)
        await self.save(ret.content)
        return ret

    async def save(self, content):
        """Save teaching plan"""
        filename = Teacher.new_file_name(self.course_title)
        pathname = WORKSPACE_ROOT / "teaching_plan"
        pathname.mkdir(exist_ok=True)
        pathname = pathname / filename
        try:
            async with aiofiles.open(str(pathname), mode='w', encoding='utf-8') as writer:
                await writer.write(content)
        except Exception as e:
            logger.error(f'Save failed：{e}')
        logger.info(f"Save to:{pathname}")

    @staticmethod
    def new_file_name(lesson_title, ext=".md"):
        """Create a related file name based on `lesson_title` and `ext`."""
        # Define the special characters that need to be replaced.
        illegal_chars = r'[#@$%!*&\\/:*?"<>|\n\t \']'
        # Replace the special characters with underscores.
        filename = re.sub(illegal_chars, '_', lesson_title) + ext
        return re.sub(r'_+', '_', filename)

    @property
    def course_title(self):
        """Return course title of teaching plan"""
        default_title = "teaching_plan"
        for act in self._actions:
            if act.topic != WriteTeachingPlanPart.COURSE_TITLE:
                continue
            if act.rsp is None:
                return default_title
            title = act.rsp.lstrip("# \n")
            if '\n' in title:
                ix = title.index('\n')
                title = title[0: ix]
            return title

        return default_title
